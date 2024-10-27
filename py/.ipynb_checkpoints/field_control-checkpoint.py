"""
These methods are an implementation of "Wide Open Spaces: A statistical technique for measuring
space creation in professional soccer."

Link: http://www.lukebornn.com/papers/fernandez_ssac_2018.pdf)
"""

import pandas as pd
import numpy as np
import sys

# add smallest possible floating-point to speed, there are some s=0 causing a divde by zero error
smoothing_param = sys.float_info.epsilon

def field_control(df_player_qry, df_play_qry, coords, grid_shape):
    """
    Calculates the offensive team field control (refered to as pitch control in 
    http://www.lukebornn.com/papers/fernandez_ssac_2018.pdf).

    Parameters
    ----------
    df_player_qry: player level tracking data, queried for a (game_id, play_id) pair
    df_play_qry: play level tracking data, queried for a (game_id, play_id) pair
    coords: the coordinate pairs that make up the field grid, as np.array([[x0,y0],[x1,y1]...[xi,yi]])
    grid_shape: tuple (x_dim, y_dim)
    
    Returns
    -------
    field_control_grid: The offensive team field control at every datapoint in the coords grid.
    """

    qb_x = df_play_qry.qb_x.values[0]
    qb_y = df_play_qry.qb_y.values[0]
    
    df_player_qry_cpy = df_player_qry.copy()
    df_player_qry_cpy['euclidean_dist_from_qb'] = np.sqrt((qb_x - df_player_qry.x)**2 +
                                                          (qb_y - df_player_qry.y)**2)

    player_dict_list = df_player_qry_cpy.to_dict(orient='records')
    sum_influence_degrees = [0.0 for val in coords]
    
    for player in player_dict_list:
        for i,p in enumerate(coords):
            influence = influence_degree(p = p.reshape(-1,1), 
                                         p_i = np.array([[player['x']],[player['y']]]), 
                                         s = player['s'] + smoothing_param, 
                                         theta=player['dir_radians'], 
                                         qb_dist=player['euclidean_dist_from_qb'])
            if player['off_def'] == 'off':
                sum_influence_degrees[i] += influence
            else:
                sum_influence_degrees[i] -= influence
        
    sum_influence_degrees = np.array(sum_influence_degrees)

    field_control = 1 / (1 + np.exp(-sum_influence_degrees))

    # Mirrored grid about the x-axis, not sure where the bug is that caused this, but mirroring
    # with [::-1, :] fixed the problem
    field_control_grid = field_control.reshape(grid_shape)[::-1, :]

    return field_control_grid

def influence_degree(p, p_i, s, theta, qb_dist):
    """
    Returns the degree of influence a player has on a point p on the field at time t

    Parameters
    ----------
    p: np.array([[x],[y]]) of given location on the field to find players influence degree at time t
    p_i: np.array([[x],[y]]) of the players coordinates at time t
    s:  speed of player at time t
    theta: direction of player in radians at time t
    qb_dist: euclidean distance of player p_i from the qb

    Returns
    -------
    Influence degree, which lies in the range [0,1]
    """
    
    return (_bivariate_gaussian_pdf(p, p_i, s, theta, qb_dist) / 
            _bivariate_gaussian_pdf(p, p, s, theta, qb_dist))


def _piecewise_function(x):
    """ Function reduces influence area radius if a player is closer to the qb """
    if x <= 18:
        return 0.01854*x**2 + 4  # Parabola for 10 < x <= 18
    else:
        return 10  # Flat line at y = 4 for x > 18

def _rotation_matrix(theta):
    return np.array([[np.cos(theta),-np.sin(theta)],
                     [np.sin(theta), np.cos(theta)]])

def _speed_ratio(s):
    return s**2 / 13**2
    
def _scaling_matrix(qb_dist, s):
    R = _piecewise_function(qb_dist)
    s_ratio = _speed_ratio(s)
    s_x = (R + (R * s_ratio)) / 2
    s_y = (R - (R * s_ratio)) / 2
    return np.array([[s_x,0],[0,s_y]])

def _mean(p_i, s_vect):
    s_unit_vector = s_vect / np.linalg.norm(s_vect)
    return p_i + (.5 * s_unit_vector)

def _cov(theta, qb_dist, s):
    S = _scaling_matrix(qb_dist, s)
    R = _rotation_matrix(theta)
    return R @ S @ S @ np.linalg.inv(R)

def _bivariate_gaussian_pdf(p, p_i, s, theta, qb_dist):
    s_x = s * np.cos(theta)
    s_y = s * np.sin(theta)
    s_vect = np.array([[s_x],[s_y]])
    
    sigma_i = _cov(theta, qb_dist, s)
    mu_i = _mean(p_i, s_vect)

    proba = 1 / np.sqrt((s*np.pi)**2 * np.linalg.det(sigma_i))
    proba += np.exp(-.5 * (p - mu_i).T @ np.linalg.inv(sigma_i) @ (p - mu_i))
    return proba[0][0]