# -*- coding: utf-8 -*-
#   Copyright (c) 2018 D. de Vries
#
#   This file is part of XRotor.
#
#   XRotor is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   XRotor is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with XRotor.  If not, see <https://www.gnu.org/licenses/>.
import numpy as np

from ctypes import c_float
from scipy.optimize import minimize, newton
from typing import Dict, Union, Iterable

array_like = Union[float, Iterable[float], np.ndarray]


class Conditions(object):
    """Propeller operating conditions

    Attributes
    ----------
    rho : float
        Air density in kg/m^3
    vso : float
        Speed of sound in m/s
    rmu : float
        Dynamic viscosity in
    vel : float
        Inflow velocity in m/s
    adv : float
        Advance ratio
        It is defined as J = V/(ωR), where J is the advance ratio, V is the inflow velocity, ω is the rotational rate in
        rad/s, and R is the blade tip radius in m.
    """

    def __init__(self,
                 rho= 0, vso=0, rmu=0,
                 alt=0, vel=0, adv=0):
        super().__init__()
        self.rho = rho
        self.vso = vso
        self.rmu = rmu
        self.alt = alt
        self.vel = vel
        self.adv = adv


class Geometry(object):
    """Propeller blade geometry definition

    Attributes
    ----------
    r_hub : float
        Hub radius in m
    r_tip : float
        Blade tip radius in m
    r_wake : float
        Wake blockage radius in m
    rake : float
        Rake angle
    geomdata : np.ndarray
        Array with the geometric data
    n_geom
    radii
    chord
    twist
    ubody
    """

    def __init__(self):
        super().__init__()
        self.r_hub = 0
        self.r_tip = 1
        self.r_wake = 0
        self.rake = 0
        self.geomdata = np.zeros((4, 0), dtype=c_float)

    @property
    def n_geom(self):
        """int: Number of points at which the geometric data is recorded."""
        return self.geomdata.shape[1]

    @n_geom.setter
    def n_geom(self, n_geom: int):
        self.geomdata.resize((4, n_geom))

    @property
    def radii(self) -> np.ndarray:
        """np.ndarray: List of normalized radial station locations."""
        return self.geomdata[0, :]

    @radii.setter
    def radii(self, radii: np.ndarray):
        if radii.size != self.geomdata.shape[1]:
            self.geomdata.resize((4, radii.size))
        self.geomdata[0, :] = radii[:]

    @property
    def chord(self) -> np.ndarray:
        """np.ndarray: List of normalized chord lengths for each radial station."""
        return self.geomdata[1, :]

    @chord.setter
    def chord(self, chord: np.ndarray):
        if chord.size != self.geomdata.shape[1]:
            self.geomdata.resize((4, chord.size))
        self.geomdata[1, :] = chord[:]

    @property
    def twist(self) -> np.ndarray:
        """np.ndarray: List of twist angles for each radial station in degrees."""
        return self.geomdata[2, :]

    @twist.setter
    def twist(self, twist: np.ndarray):
        if twist.size != self.geomdata.shape[1]:
            self.geomdata.resize((4, twist.size))
        self.geomdata[2, :] = twist[:]

    @property
    def ubody(self) -> np.ndarray:
        """np.ndarray: Nacelle perturbation axial velocities at each radial station in m/s."""
        return self.geomdata[3, :]

    @ubody.setter
    def ubody(self, ubody: np.ndarray):
        if ubody.size != self.geomdata.shape[1]:
            self.geomdata.resize((4, ubody.size))
        self.geomdata[3, :] = ubody[:]


class Section(object):
    """Aerodynamic section definition

    Attributes
    ----------
    a_0 : float
        Zero-lift angle of attack in degrees.
    dClda : float
        Lift curve slope, d(C_l)/d(alpha), in the linear regime in 1/rad.
    Cl_min, Cl_min : float
        Lift coefficients at the positive and negative stall points.
    dClda_stall : float
        Lift curve slope in the stalled part of the lift curve in 1/rad.
    dCl_stall : float
        Lift increment from the end of the linear range to stall.
    Cd_min : float
        Minimum drag coefficient.
    Cl_Cd_min : float
        Lift coefficient when the drag coefficient is at its minimum.
    dCddCl2 : float
        Quadratic drag polar coefficient, d(C_d)/d(C_l^2).
    Cm_const : float
        Moment coefficient in the linear regime, which is assumed to be constant.
    M_crit : float
        Critical Mach number.
    Re : float
        Reference Reynolds number.
    Re_exp : float
        Exponential correction coefficient to correct for Reynolds number increments due to induced velocities.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.a_0 = 0. if len(args) < 1 else args[0]
        self.dClda = 0. if len(args) < 2 else args[1]
        self.Cl_max = 0. if len(args) < 3 else args[2]
        self.Cl_min = 0. if len(args) < 4 else args[3]
        self.dClda_stall = 0. if len(args) < 5 else args[4]
        self.dCl_stall = 0. if len(args) < 6 else args[5]
        self.Cd_min = 0. if len(args) < 7 else args[6]
        self.Cl_Cd_min = 0. if len(args) < 8 else args[7]
        self.dCddCl2 = 0. if len(args) < 9 else args[8]

        self.Cm_const = 0. if 'Cm_const' not in kwargs else kwargs['Cm_const']
        self.M_crit = 0. if 'M_crit' not in kwargs else kwargs['M_crit']
        self.Re = 0. if 'Re' not in kwargs else kwargs['Re']
        self.Re_exp = 0. if 'Re_exp' not in kwargs else kwargs['Re_exp']

    @staticmethod
    def from_dict(d):
        """Create an instance of the Section class from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing relevant aerodynamic properties

        Returns
        -------
        Section
            Instance of this class with the data provided through the dictionary
        """
        sec = Section()
        for key, value in d.items():
            if hasattr(sec, key):
                setattr(sec, key, value)
        return sec

    @staticmethod
    def fit_polar(polar: np.ndarray) -> object:
        """Fit the aerodynamic Section properties to a given polar.

        Parameters
        ----------
        polar : np.ndarray
            Polar generated by an appropriate 2D airfoil analysis program or experimental results. This array should
            have at least 4 columns in the following order: angle of attack in degrees, lift coefficient, drag
            coefficient, and moment coefficient. There should be a sufficient number of rows.

        Returns
        -------
        Section
            An instance of the Section class with all model parameters specified to provide the best possible
            fit to the polar data.
        """
        a = polar[:, 0]
        cl = polar[:, 1]
        cd = polar[:, 2]

        def e(x):
            return np.sqrt(np.mean((Section(*x).cl(a) - cl) ** 2)) + \
                   np.sqrt(np.mean((Section(*x).cd(a) - cd) ** 2))

        res = minimize(e, np.ones(9),
                       bounds=[(-10., 10.), (1., 20.), (0., 3.), (-3., 0.), (-2., 2.), (0.1, 0.3),
                               (0., 0.5), (-1., 1.), (0., 1.)])

        if polar.shape[1] == 9:
            # Cp is included
            a_unique, indices = np.unique(polar[:, 0], return_index=True)
            cp = np.interp(0., a_unique, polar[indices, 5])

            gamma = 1.4

            def f(M):
                return ((2. / (gamma * M ** 2)) *
                        (((gamma + 1.) / (2 * (1 + .5 * (gamma - 1) * M ** 2))) ** (gamma / (1 - gamma)) - 1)) - cp

            def df(M):
                a = ((-4. / (gamma * M ** 3)) *
                     (((gamma + 1.) / (2 * (1 + .5 * (gamma - 1) * M ** 2))) ** (gamma / (1 - gamma)) - 1))
                b = -(2. / (gamma * M ** 2)) * (gamma / (1 - gamma)) * \
                    ((gamma + 1.) / (2 * (1 + .5 * (gamma - 1) * M ** 2))) ** (gamma / (1 - gamma) - 1) * \
                    ((gamma + 1) / (2 * (1 + .5 * (gamma - 1) * M ** 2)) ** 2) * 2 * (gamma - 1) * M
                return a + b

            M_crit = newton(f, 1., df)
        else:
            M_crit = 0.6

        return Section(*res.x, Cm_const=np.mean(polar[:, 4]), M_crit=M_crit)

    def cl_lin(self, alpha: array_like) -> array_like:
        """Calculate the lift coefficient in the linear range for a given angle of attack.

        Parameters
        ----------
        alpha : array-like
            One or more angles of attack in degrees.

        Returns
        -------
            Linear lift coefficients for each specified angle of attack.
        """
        return (alpha - self.a_0) * np.pi / 180. * self.dClda

    def delta_cl_nl(self, alpha: array_like) -> array_like:
        """Calculate the offset of the lift coefficient in the non-linear range for a given angle of attack.

        Parameters
        ----------
        alpha : array-like
            One or more angles of attack in degrees.

        Returns
        -------
            Offset of the lift coefficients for each specified angle of attack.
        """
        cl_lin = self.cl_lin(alpha)
        return self.dCl_stall * np.log((1 + np.exp((cl_lin - self.Cl_max) / self.dCl_stall)) /
                                       (1 + np.exp((self.Cl_min - cl_lin) / self.dCl_stall)))

    def cl(self, alpha: Union[float, Iterable[float], np.ndarray]) -> Union[float, Iterable[float], np.ndarray]:
        """Calculate the lift coefficient for a given angle of attack.

        Parameters
        ----------
        alpha : float or iterable of floats or np.ndarray
            One or more angles of attack in degrees.

        Returns
        -------
            Lift coefficients for each specified angle of attack.
        """
        return self.cl_lin(alpha) - (1 - self.dClda_stall / self.dClda) * self.delta_cl_nl(alpha)

    def cd_lin(self, alpha: array_like) -> array_like:
        """Calculate the drag coefficient in the linear range for a given angle of attack.

        Parameters
        ----------
        alpha : array-like
            One or more angles of attack in degrees.

        Returns
        -------
            Linear drag coefficients for each specified angle of attack.
        """
        return self.Cd_min + self.dCddCl2 * (self.cl(alpha) - self.Cl_Cd_min) ** 2

    def delta_cd_nl(self, alpha: array_like) -> array_like:
        """Calculate the offset of the drag coefficient in the non-linear range for a given angle of attack.

        Parameters
        ----------
        alpha : array-like
            One or more angles of attack in degrees.

        Returns
        -------
            Offset of the drag coefficients for each specified angle of attack.
        """
        return 2 * ((1 - self.dClda_stall / self.dClda) * self.delta_cl_nl(alpha) / self.dClda) ** 2

    def cd(self, alpha: array_like) -> array_like:
        """Calculate the drag coefficient for a given angle of attack.

        Parameters
        ----------
        alpha : array-like
            One or more angles of attack in degrees.

        Returns
        -------
            Drag coefficients for each specified angle of attack.
        """
        return self.cd_lin(alpha) + self.delta_cd_nl(alpha)


class Blade(object):
    """Propeller blade definition

    Attributes
    ----------
    geometry : Geometry
        Instance of the Geometry class representing the geometry of the blade
    sections : dict of Section instances by float
        Dictionary of aerodynamic Sections, indexed by their normalized radial positions along the blade
    n_aero
    aerodata
    geomdata
    """

    def __init__(self, geometry: Geometry = Geometry(), sections: Dict[float, Section] = None):
        super().__init__()
        self.geometry: Geometry = geometry
        self.sections: Dict[float, sections] = dict() if sections is None else sections

    @property
    def n_aero(self) -> int:
        """int: Number of aerodynamic Sections"""
        return len(self.sections)

    @property
    def aerodata(self) -> np.ndarray:
        """np.ndarray: Array with all Sections' data, row-wise, indexed by radial position in the first column"""
        data = np.zeros((14, self.n_aero), dtype=c_float, order='F')
        for i, key in enumerate(sorted(self.sections.keys())):
            sec = self.sections[key]
            data[0][i] = key
            data[1][i] = sec.a_0
            data[2][i] = sec.Cl_max
            data[3][i] = sec.Cl_min
            data[4][i] = sec.dClda
            data[5][i] = sec.dClda_stall
            data[6][i] = sec.dCl_stall
            data[7][i] = sec.Cd_min
            data[8][i] = sec.Cl_Cd_min
            data[9][i] = sec.dCddCl2
            data[10][i] = sec.Cm_const
            data[11][i] = sec.M_crit
            data[12][i] = sec.Re
            data[13][i] = sec.Re_exp
        return data

    @property
    def geomdata(self) -> np.ndarray:
        """np.ndarray: Array of the blade's geometric data"""
        return self.geometry.geomdata


class Disk(object):
    """Propeller disk definition

    Attributes
    ----------
    n_blds : int
        Number of blades
    blade : Blade
        Definition of the blade
    """

    def __init__(self, n_blds: int = 0, blade: Blade = Blade()):
        super().__init__()
        self.n_blds: int = n_blds
        self.blade: Blade = blade


class Settings(object):
    """XRotor run case settings

    Attributes
    ----------
    free : bool
        True for free wake formulation
    duct : bool
        True if a duct is present
    wind : bool
        True if windmill-mode plotting is to be used
    """

    def __init__(self, free=True, duct=False, wind=False):
        super().__init__()
        self.free = free
        self.duct = duct
        self.wind = wind


class Case(object):
    """XRotor run case definition

    Attributes
    ----------
    conditions : Conditions
        Specification of the operating conditions
    disk : Disk
        Definition of the propeller disk
    settings : Settings
        Specification of the run case settings
    """

    def __init__(self,
                 conditions: Conditions = Conditions(),
                 disk: Disk = Disk(), settings: Settings = Settings()):
        super().__init__()
        self.conditions: Conditions = conditions
        self.disk: Disk = disk
        self.settings: Settings = settings

    @staticmethod
    def from_dict(d):
        """Construct an instance of this class from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary representing an XRotor run case

        Returns
        -------
        Case
            Instance of this class corresponding to the data passed through the dictionary
        """
        case = Case()

        def recurse(obj, sub_d):
            if isinstance(obj, dict):
                for key, value in sub_d.items():
                    obj.update({key: Section.from_dict(value)})
            else:
                for key, value in sub_d.items():
                    if hasattr(obj, key):
                        if isinstance(value, dict):
                            recurse(getattr(obj, key), value)
                        else:
                            setattr(obj, key, value)
        recurse(case, d)
        return case


class Performance(object):
    """Blade performance specification

    Attributes
    ----------
    rpm
    thrust
    torque
    power
    efficiency
    """

    def __init__(self, rpm: float = 0, thrust: float = 0, torque: float = 0, power: float = 0, efficiency: float = 0):
        super().__init__()
        self._rpm: c_float = c_float(rpm)
        self._thrust: c_float = c_float(thrust)
        self._torque: c_float = c_float(torque)
        self._power: c_float = c_float(power)
        self._efficiency: c_float = c_float(efficiency)

    @property
    def rpm(self):
        """float: Rotational speed in rev/min"""
        return self._rpm.value

    @property
    def thrust(self):
        """float: Thrust in N"""
        return self._thrust.value

    @property
    def torque(self):
        """float: Torque in Nm"""
        return self._torque.value

    @property
    def power(self):
        """float: Power in W"""
        return self._power.value

    @property
    def efficiency(self):
        """float: Overall efficiency"""
        return self._efficiency.value

