from typing import Optional, Any, Tuple, Dict, List, Union
import numpy as np
import math

from .. import display, throw_G2L_warning, log_error, log_warn, log_info, log_debug, log_trace, log_subtrace

from . import step, span, find_roots, find_global_max, correct_limits

### FFT AND PSD COMPUTATIONS
def dual(arr:np.ndarray) -> np.ndarray:
    return np.fft.fftshift(np.fft.fftfreq(len(arr), step(arr)))

def rdual(arr:np.ndarray) -> np.ndarray:
    return np.fft.rfftfreq(len(arr), step(arr))

from scipy.signal.windows import get_window # FFT windowing

def ft1d(arr:np.ndarray, window:str= 'hann', norm=None) -> np.ndarray:
    """

    Parameters
    ----------
    arr
    window
    norm

    Returns
    -------

    """
    N = len(arr)
    z_treated = arr * get_window(window, N)
    # z_treated -= np.mean(z_treated) * (1-1e-12) # this is to avoid having zero amplitude and problems when taking the log
    z_treated -= np.mean(z_treated)

    z_hat = np.fft.rfft(z_treated, norm=norm)
    return z_hat

def ft2d(arr:np.ndarray, window:str='hann', norm=None) -> np.ndarray:
    Nt, Nx = arr.shape
    z_treated = arr * np.expand_dims(get_window(window, Nt), axis=1) * np.expand_dims(get_window(window, Nx), axis=0)
    # z_treated -= np.mean(z_treated) * (1-1e-12) # this is to avoid having zero amplitude and problems when taking the log
    z_treated -= np.mean(z_treated)

    z_hat = np.fft.rfft2(z_treated, norm=norm)
    return np.fft.fftshift(z_hat, axes=0)
    # return np.concatenate((z_hat[(Nt+1)//2:,:], z_hat[:(Nt+1)//2,:])) # reorder bcz of the FT

def window_factor(window:str):
    """
    Returns the factor by which the energy is multiplied when the signal is windowed

    Parameters
    ----------
    window

    Returns
    -------

    """
    if window is None:
        return 1.
    elif window == 'boxcar':
        return 1.
    elif window == 'hann':
        return 8/3
    else:
        return 1/((get_window(window, 1000)**2).sum()/1000)

def psd1d(z, x, window:str= 'hann') -> np.ndarray:
    z_ft = ft1d(z, window=window, norm="backward") * step(x) # x dt for units
    # energy spectral density: energy of the signal at this frequency
    # useful for time-limited signals (impulsions)
    esd = np.abs(z_ft)**2 * window_factor(window)
    esd[1:] *= 2 # x 2 because of rfft which truncates the spectrum (except the 0 harmonic)
    # psd = esd / T
    return esd / span(x)

def psd2d(z, x, y, window:str= 'hann') -> np.ndarray:
    y_ft = ft2d(z, window=window, norm="backward") * step(x) * step(y) # x dt for units
    # energy spectral density: energy of the signal at this frequency
    # useful for time-limited signals (impulsions)
    esd = np.abs(y_ft)**2 * window_factor(window)**2
    esd[:, 1:] *= 2 # x 2 because of rfft which truncates the spectrum (except the 0 harmonic)
    # psd = esd / (T X)
    return esd / span(x) / span(y)

#
def estimatesignalfrequency(z, x=None, window:str= 'hann') -> float:
    if x is None:
        x = np.arange(len(z))
    fx:np.ndarray = rdual(x)
    pw:np.ndarray = psd1d(z, x, window=window)
    return find_global_max(fx, pw)


# find the edges of the peak (1D, everything is easy)
def attenuate_power(value, attenuation_factor_dB):
    return value / math.pow(10, attenuation_factor_dB / 20)
def peak_contour1d(peak_x, z, peak_depth_dB, x=None):
    if x is None:
        x = np.arange(z.shape[0])
    peak_index = np.argmin((x - peak_x) ** 2)
    zintercept = attenuate_power(z[peak_index], peak_depth_dB)
    x1_intercept = find_roots(x, z - zintercept)
    x1_before = peak_x
    x1_after = peak_x
    if len(x1_intercept[x1_intercept < peak_x] > 0):
        x1_before = x1_intercept[x1_intercept < peak_x].max()
    if len(x1_intercept[x1_intercept > peak_x] > 0):
        x1_after = x1_intercept[x1_intercept > peak_x].min()
    return x1_before, x1_after
def peak_vicinity1d(peak_x, z, peak_depth_dB, x=None):
    if x is None:
        x = np.arange(z.shape[0])
    x1_before, x1_after = peak_contour1d(peak_x=peak_x, z=z, peak_depth_dB=peak_depth_dB, x=x)
    # return np.where((x1 >= x1_before)*(x1 <= x1_after))[0]
    return ((x >= x1_before) * (x <= x1_after)).astype(bool)

def power_near_peak1d(peak_x, z, peak_depth_dB, x=None):
    # powerlog_intercmor_incertitude = zmeanx_psd.max()/(10**(peak_depth_dB/10))
    # freq_for_intercept = utility.find_roots(freqs, zmeanx_psd - powerlog_intercmor_incertitude)
    # freqpre = freq_for_intercept[freq_for_intercept < freq_guess].max()
    # freqpost = freq_for_intercept[freq_for_intercept > freq_guess].min()
    # integrate the PSD along the peak
    # ### (abandoned) do a trapezoid integration
    # x_f = np.concatenate(([freqpre], freqs[(freqpre < freqs)*(freqs < freqpost)], [freqpost]))
    # y_f = np.concatenate(([np.interp(freqpre, freqs, zmeanx_psd)], zmeanx_psd[(freqpre < freqs)*(freqs < freqpost)], [np.interp(freqpost, freqs, zmeanx_psd)]))
    # p_ft_peak = trapezoid(y_f, x_f)
    ### Go bourrin (we are in log we do not care) : rectangular integration
    # p_ft_peak = np.sum(zmeanx_psd[(freqpre < freqs)*(freqs < freqpost)]) * utility.step(freqs)
    return np.sum(z[peak_vicinity1d(peak_x=peak_x, z=z, peak_depth_dB=peak_depth_dB, x=x)]) * step(x)

### 2D peak finding (life is pain)
# TODO: Simplify this. We use multipolygons BUT it seems that every multipolygon we have does in fact contain only one polygon
# TODO: Which is dumb. We might be able to change that just by setting multipolygon = multipolygon.geoms[0] but honestly who has time for that ?

from contourpy import contour_generator, ZInterp, convert_filled
# from contourpy import convert_multi_filled # todo: works when contourpy >= 1.3, we have 1.2

### SHAPELY SHENANIGANS

from shapely import GeometryType, from_ragged_array, Point, LinearRing

def find_shapely_contours(contourgenerator, zintercept):
    contours = contourgenerator.filled(zintercept, np.inf)
    polygons = [([contours[0][i]], [contours[1][i]]) for i in range(len(contours[0]))]
    # polygons_for_shapely = convert_multi_filled(polygons, cg.fill_type, "ChunkCombinedOffsetOffset") # todo: works when contourpy >= 1.3, we have 1.2
    polygons_for_shapely = [convert_filled(polygon, contourgenerator.fill_type, "ChunkCombinedOffsetOffset") for polygon in polygons]

    log_trace(f'Found {len(polygons)} contours')

    multipolygons = []
    for i_poly in range(len(polygons_for_shapely)):
        points, offsets, outer_offsets = polygons_for_shapely[i_poly][0][0], polygons_for_shapely[i_poly][1][0], polygons_for_shapely[i_poly][2][0]
        multipolygon = from_ragged_array(GeometryType.MULTIPOLYGON, points, (offsets, outer_offsets, [0, len(outer_offsets)-1]))[0]
        # multipolygon = from_ragged_array(GeometryType.POLYGON, points, (offsets, outer_offsets)) # try to do a shapely Polygon is better if we really need to handle the holes
        multipolygons.append(multipolygon)
    return multipolygons
def contour_containspoint(contour, point:Tuple[float, float]) -> bool:
    """Returns whether or not the points are contained in the contour."""
    return contour.contains(Point(point[0], point[1]))
def contour_containspoints(contour, points:List[Tuple[float, float]]) -> np.ndarray:
    """Returns whether or not the points are contained in the contour."""
    return np.array([contour.contains(Point(point[0], point[1])) for point in points]).astype(bool)
def contours_containsanyofthepoints(contours, points:List[Tuple[float, float]]) -> np.ndarray:
    """Returns wheter any of the points are contained in the contours."""
    return np.array([contour_containspoints(contour, points).any() for contour in contours])
def contours_areas(contours, scale_factor_x, scale_factor_y, condition:Optional[np.ndarray[bool]]=None) -> np.ndarray:
    """Returns the area of a contour, in px² if the scale factors are right."""
    if condition is None:
        condition = np.ones(len(contours), dtype=bool)
    areas = np.ones(len(contours), dtype=float)
    for i, contour in enumerate(contours):
        if condition[i]:
            areas[i] = contour.area/scale_factor_x/scale_factor_y
    return areas
def contours_perimeters(contours, scale_factor_x, scale_factor_y, condition:Optional[np.ndarray[bool]]=None):
    """Returns the perimeter of a contour, in px if the scale factors are right."""
    log_trace(f'Perimeters of {len(contours)} contours')
    if condition is None:
        condition = np.ones(len(contours), dtype=bool)
    perimeters = np.ones(len(contours), dtype=float)
    for i, contour in enumerate(contours):
        if condition[i]:
            log_subtrace(f'contour {i}: type: {contour.geom_type}')
            log_subtrace(f'contour {i}: contained geometries: {len(contour.geoms)}')
            hull = contour.geoms[0]
            log_subtrace(f'contour {i}: hull is : {hull.geom_type}')
            log_subtrace(f'contour {i}: hull boundary is : {hull.boundary.geom_type}')
            log_subtrace(f'contour {i}: hull exterior is : {hull.exterior.geom_type}')
            log_subtrace(f'contour {i}: hull interior contains {len(hull.interiors)} rings')
            all_boundaries = [hull.exterior] + [interior for interior in hull.interiors]
            p = 0
            for boundary in all_boundaries:
                line = np.array(boundary.coords)
                line[:, 0] /= scale_factor_x
                line[:, 1] /= scale_factor_y
                p += LinearRing(line).length
            perimeters[i] = p
    return perimeters
def draw_multipolygon_edge(ax, multipolygon, xmin=None, **kwargs):
    for geom in multipolygon.geoms:
        log_subtrace(f'geom is : {geom.geom_type}')
        log_subtrace(f'geom boundary is : {geom.boundary.geom_type}')
        log_subtrace(f'geom exterior is : {geom.exterior.geom_type}')
        log_subtrace(f'geom interior contains {len(geom.interiors)} rings')
        all_boundaries = [geom.exterior] + [interior for interior in geom.interiors]
        for boundary in all_boundaries:
            line = np.array(boundary.coords)
            if xmin is not None:
                line[:, 0][line[:, 0] < xmin] = xmin
            ax.plot(line[:,0], line[:,1], **kwargs)


### CONTOUR FINDING 2D AND PEAK MEASUREMENT
peak_max_area_default = 100
peak_min_circularity_default = .3

def peak_contour2d(peak_x:float, peak_y:float, z:np.ndarray, peak_depth_dB:float, x:Optional[np.ndarray[float]]=None, y:Optional[np.ndarray[float]]=None,
                   fastmode:bool=True, peak_max_area:Optional[float]=None, peak_min_circularity:Optional[float]=None):
    """Finds a contour around a peak at a certain threshold level

    Parameters
    ----------
    peak_x
    peak_y
    z
    peak_depth_dB
    x
    y
    fastmode : do not compute aeras and perimeters of contour that do not contain the peak
    peak_max_area : dmaximum area, in px²
    peak_min_circularity : minimum circularity ([0-1]), for reasonable contours

    Returns
    -------

    """
    if x is None:
        x = np.arange(z.shape[1])
    if y is None:
        y = np.arange(z.shape[0])
    if peak_max_area is None:
        global peak_max_area_default
        peak_max_area = peak_max_area_default
    if peak_min_circularity is None:
        global peak_min_circularity_default
        peak_min_circularity = peak_min_circularity_default

    log_debug(f'Searching for a contour around ({round(peak_x, 3)}, {round(peak_y, 3)}) with attenuation -{peak_depth_dB} dB')

    interestpoints = [[peak_x, peak_y]]
    if np.isclose(peak_x, 0):
        interestpoints.append([peak_x, -peak_y])
    zpeak = z[np.argmin((y - peak_y) ** 2)][np.argmin((x - peak_x) ** 2)]

    # duplicate the first column to better find the points which are at k=0
    x_for_cg = np.concatenate(([x[0]-step(x)], x))
    y_for_cg = y.copy()
    z_for_cg = np.zeros((z.shape[0], z.shape[1]+1))
    z_for_cg[:, 1:] = z
    z_for_cg[:, 0] = z[:, 0]
    # to find the contour, we use contourpy which is fast, efficient and has the log-interpolation option that is relevant for us
    cg = contour_generator(x=x_for_cg, y=y_for_cg, z=z_for_cg, z_interp=ZInterp.Log, fill_type="OuterOffset")

    min_peak_depth_dB = 10

    while peak_depth_dB > 0: # infinite loop, return is in it
        zintercept = attenuate_power(zpeak, peak_depth_dB)

        multipolygons = find_shapely_contours(cg, zintercept)

        containspeak = contours_containsanyofthepoints(multipolygons, interestpoints)
        areas = contours_areas(multipolygons, step(x), step(y), condition=containspeak if fastmode else None)
        perimeters = contours_perimeters(multipolygons, step(x), step(y), condition=containspeak if fastmode else None)
        circularities = 4*np.pi*areas / perimeters**2

        for i in range(len(multipolygons)):
            if containspeak[i] or not fastmode:
                log_subtrace(f'multipoligon {i}: centroid: {multipolygons[i].centroid}')
                log_subtrace(f'multipoligon {i}: area: {round(areas[i], 1)} px^2, limit is {peak_max_area}')
                log_subtrace(f'multipoligon {i}: perimeter: {round(perimeters[i], 1)} px')
                log_subtrace(f'multipoligon {i}: circularity: {round(circularities[i], 3)} [0-1], limit is {peak_min_circularity}')

        isnottoobig = areas < peak_max_area
        iscircularenough = circularities > peak_min_circularity

        contour_is_valid = containspeak * isnottoobig * iscircularenough

        log_trace(f'Contains peak: {containspeak if not fastmode else containspeak[containspeak]}')
        log_trace(f'Not too big:   {isnottoobig if not fastmode else isnottoobig[containspeak]}')
        log_trace(f'Circular:      {iscircularenough if not fastmode else iscircularenough[containspeak]}')
        log_trace(f'Valid contour: {contour_is_valid if not fastmode else contour_is_valid[containspeak]}')

        # find the contour that contains the point
        if contour_is_valid.any() or peak_depth_dB == min_peak_depth_dB:
            maincontours = [multipolygons[index] for index in np.where(contour_is_valid == True)[0]]
            log_debug(f"Found {len(maincontours)} valid contours.")
            return maincontours
        else:
            peak_depth_dB -= 10
            if peak_depth_dB < min_peak_depth_dB: peak_depth_dB = min_peak_depth_dB
            log_debug(f"Couldn't find any valid contour: Trying peak_depth={peak_depth_dB} dB")
    if peak_depth_dB != min_peak_depth_dB:
        peak_depth_dB = min_peak_depth_dB
        log_debug(f"Couldn't find any valid contour: Trying peak_depth={peak_depth_dB} dB")

def grid_points_in_contour(contour, x:np.ndarray[float], y:np.ndarray[float]) -> np.ndarray:
    incontour = np.zeros((len(y), len(x)), dtype=bool)
    xmin, ymin, xmax, ymax = contour.bounds
    for i_x in np.where((x >= xmin)*(x <= xmax))[0]:
        for i_y in np.where((y >= ymin)*(y <= ymax))[0]:
            incontour[i_y, i_x] = contour_containspoint(contour, (x[i_x], y[i_y]))
    return incontour

def peak_vicinity2d(peak_x, peak_y, z:np.ndarray[np.ndarray[float]], peak_depth_dB, x=Optional[np.ndarray[float]], y=Optional[np.ndarray[float]],
                    peak_contours:Optional[List]=None,
                    peak_max_area:Optional[float]=None, peak_min_circularity:Optional[float]=None):
    if x is None:
        x = np.arange(z.shape[1])
    if y is None:
        y = np.arange(z.shape[0])
    log_debug(f'Searching for the vicinity of  ({round(peak_x, 3)}, {round(peak_y, 3)})')

    if peak_contours is None:
        peak_contours = peak_contour2d(peak_x=peak_x, peak_y=peak_y, z=z, peak_depth_dB=peak_depth_dB, x=x, y=y,
                                       peak_max_area=peak_max_area, peak_min_circularity=peak_min_circularity)

    # make a mask with the points inside the contourS
    mask = np.zeros_like(z).astype(bool)
    # take at least the interest point
    mask[np.argmin((y - peak_y) ** 2)][np.argmin((x - peak_x) ** 2)] = True
    for contour in peak_contours:
        contour_mask = grid_points_in_contour(contour, x, y)

        mask = np.bitwise_or(mask, contour_mask)

    log_debug(f'Found a vicinity of area {mask.sum()} px²')

    return mask
def power_near_peak2d(peak_x, peak_y, z, peak_depth_dB, x=None, y=None,
                      peak_contours:Optional[List]=None, peak_vicinity:Optional[np.ndarray]=None,
                      peak_max_area:Optional[float]=None, peak_min_circularity:Optional[float]=None):
    log_debug(f'Measuring the power around     ({round(peak_x, 3)}, {round(peak_y, 3)})')
    if peak_vicinity is None:
        peak_vicinity = peak_vicinity2d(peak_x=peak_x, peak_y=peak_y, z=z, peak_depth_dB=peak_depth_dB, x=x, y=y,
                                        peak_contours=peak_contours,
                                        peak_max_area=peak_max_area, peak_min_circularity=peak_min_circularity)
    pw = np.sum(z[peak_vicinity]) * step(x) * step(y)
    log_debug(f'Power: {pw} (amplitude: {np.sqrt(pw)*np.sqrt(2)})')
    return pw