# -*- coding: utf-8 -*-

' a module for plotting the RDM '

__author__ = 'Zitong Lu'

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from nilearn import plotting, datasets, surface
import nibabel as nib
from neurora.stuff import get_affine, correct_by_threshold, get_bg_ch2, get_bg_ch2bet

def plot_rdm(rdm, rescale=False, conditions=None, con_fontsize=12):

    if len(np.shape(rdm)) != 2:

        return None

    a, b = np.shape(rdm)

    if a != b:

        return None

    cons = rdm.shape[0]

    if rescale == True:

        vrdm = np.reshape(rdm, [cons*cons])
        svrdm = set(vrdm)
        lvrdm = list(svrdm)
        lvrdm.sort()
        maxvalue = lvrdm[-1]
        minvalue = lvrdm[1]
        for i in range(cons):
            for j in range(cons):
                if i != j:
                    rdm[i, j] = float((rdm[i, j]-minvalue)/(maxvalue-minvalue))

    plt.imshow(rdm, extent=(0, 1, 0, 1), cmap=plt.cm.jet, clim=(0, 1))

    #plt.axis("off")
    cb = plt.colorbar()
    cb.ax.tick_params(labelsize=16)
    font = {'size': 18}
    if rescale == True:
        cb.set_label("Dissimilarity (Rescaling)", fontdict=font)
    elif rescale == False:
        cb.set_label("Dissimilarity", fontdict=font)

    if conditions != None:
        print("1")
        step = float(1/cons)
        x = np.arange(0.5*step, cons*step-0.5*step, step)
        y = np.arange(cons*step-0.5*step, 0.5*step, -step)
        plt.xticks(x, conditions, fontsize=con_fontsize, rotation=30, ha="right")
        plt.yticks(y, conditions, fontsize=con_fontsize)

    plt.show()

def plot_rdm_withvalue(rdm, value_fontsize=10, conditions=None, con_fontsize=12):

    cons = rdm.shape[0]

    if len(np.shape(rdm)) != 2:

        return None

    a, b = np.shape(rdm)

    if a != b:

        return None

    plt.imshow(rdm, cmap=plt.cm.Greens, clim=(0, 1))

    plt.axis("off")

    for i in range(a):
        for j in range(b):
            text = plt.text(i, j, float('%.4f'%rdm[i, j]),
                           ha="center", va="center", color="blue", fontsize=value_fontsize)

    cb = plt.colorbar()
    cb.ax.tick_params(labelsize=16)
    font = {'size': 18}
    cb.set_label("Dissimilarity", fontdict=font)

    if conditions != None:
        print("1")
        step = float(1/cons)
        x = np.arange(0.5*step, cons*step-0.5*step, step)
        y = np.arange(cons*step-0.5*step, 0.5*step, -step)
        plt.xticks(x, conditions, fontsize=con_fontsize, rotation=30, ha="right")
        plt.yticks(y, conditions, fontsize=con_fontsize)

    plt.show()

def plot_corrs_by_time(corrs, labels=None, time_unit=[0, 0.1]):
    # corrs represent the correlation coefficients point-by-point, its shape :
    #       [n, ts, 2] (here 2 contains r-value and p-value) or [n, ts] (r-value)
    # label represent the conditions of RSA results, its shape : [n]
    # time_unit=[start_t, t_step]

    n = corrs.shape[0]
    ts = corrs.shape[1]

    start_t = time_unit[0]
    tstep = time_unit[1]

    end_t = start_t + ts * tstep

    x = np.arange(start_t, end_t, tstep)

    t = ts * 50

    x_soft = np.linspace(x.min(), x.max(), t)

    y_soft = np.zeros([n, t])

    for i in range(n):
        if len(corrs.shape) == 3:
            f = interp1d(x, corrs[i, :, 0], kind='cubic')
            y_soft[i] = f(x_soft)
        if len(corrs.shape) == 2:
            f = interp1d(x, corrs[i, :], kind='cubic')
            y_soft[i] = f(x_soft)

    vmax = np.max(y_soft)
    vmin = np.min(y_soft)

    if vmax <= 1/1.1:
        ymax = np.max(y_soft)*1.1
    else:
        ymax = 1

    if vmin >= 0:
        ymin = -0.1
    elif vmin < 0 and vmin > -1/1.1:
        ymin = np.min(y_soft)*1.1
    else:
        ymin = -1

    fig, ax = plt.subplots()

    for i in range(n):
        if labels:
            plt.plot(x_soft, y_soft[i], linewidth=3, label=labels[i])
        else:
            plt.plot(x_soft, y_soft[i], linewidth=3)

    plt.ylim(ymin, ymax)
    plt.ylabel("Similarity", fontsize=20)
    plt.xlabel("Time (s)", fontsize=20)
    plt.tick_params(labelsize=18)

    if labels:
        plt.legend()

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.show()

def plot_corrs_hotmap(eegcorrs, chllabels=[], time_unit=[0, 0.1], lim=[0, 1], smooth=True):
    # eegcorrs represents the correlation coefficients time-by-time, its shape:
    # [N_chls, ts, 2] or [N_chls, ts], N_chls: number of channels, ts: number of time points, 2: a r-value and a p-value
    # chllabel represents the names of channels
    # time_unit=[start_t, t_step]
    # smooth represents smoothing the results or not

    nchls = eegcorrs.shape[0]
    ts = eegcorrs.shape[1]

    start_t = time_unit[0]
    tstep = time_unit[1]

    end_t = start_t + ts * tstep

    x = np.arange(start_t, end_t, tstep)

    for i in range(nchls):
        if i % 10 == 0 and i != 10:
            newlabel = str(i+1) + "st"
        elif i % 10 == 1 and i != 11:
            newlabel = str(i+1) + "nd"
        elif i % 10 == 2 and i != 12:
            newlabel = str(i+1) + "rd"
        else:
            newlabel = str(i+1) + "th"
        chllabels.append(newlabel)

    if smooth == True:

        t = ts * 50

        x_soft = np.linspace(x.min(), x.max(), t)

        y_soft = np.zeros([nchls, t])

        for i in range(nchls):
            if len(eegcorrs.shape) == 3:
                f = interp1d(x, eegcorrs[i, :, 0], kind='cubic')
                y_soft[i] = f(x_soft)
            elif len(eegcorrs.shape) == 2:
                f = interp1d(x, eegcorrs[i, :], kind='cubic')
                y_soft[i] = f(x_soft)

        rlts = y_soft

    if smooth == False:
        if len(eegcorrs.shape) == 3:
            rlts = eegcorrs[:, :, 0]
        elif len(eegcorrs.shape) == 2:
            rlts = eegcorrs

    print(rlts.shape)

    fig = plt.gcf()
    fig.set_size_inches(10, 3)

    limmin = lim[0]
    limmax = lim[1]
    plt.imshow(rlts, extent=(float(start_t*nchls/3), float(end_t*nchls/3), 0, 0.16*nchls), clim=(limmin, limmax), origin='low')

    cb = plt.colorbar()
    cb.ax.tick_params(labelsize=16)
    font = {'size': 18}
    cb.set_label("Similarity", fontdict=font)
    xi = []
    for i in range(nchls):
        xi.append(0.16*i + 0.08)
    yi = chllabels
    plt.tick_params(labelsize=18)
    plt.yticks(xi, yi, fontsize=18)
    plt.ylabel("Channel", fontsize=20)
    plt.xlabel("Time (s)", fontsize=20)
    plt.show()

def plot_brainrsa_regions(img, threshold=None, background=get_bg_ch2()):

    if threshold != None:

        imgarray = nib.load(img).get_data()
        affine = get_affine(img)

        imgarray = correct_by_threshold(imgarray, threshold)

        img = nib.Nifti1Image(imgarray, affine)

    plotting.plot_roi(roi_img=img, bg_img=background, threshold=0, vmin=0.1, vmax=1, title="Similarity", resampling_interpolation="continuous")

    plt.show()

def plot_brainrsa_montage(img, threshold=None, slice=[6, 6, 6], background=get_bg_ch2bet()):

    if threshold != None:

        imgarray = nib.load(img).get_data()
        affine = get_affine(img)

        imgarray = correct_by_threshold(imgarray, threshold)

        img = nib.Nifti1Image(imgarray, affine)

    slice_x = np.shape(slice)[0]
    slice_y = np.shape(slice)[1]
    slice_z = np.shape(slice)[2]

    if slice_x != 0:
        plotting.plot_stat_map(stat_map_img=img, bg_img=background, display_mode='x', cut_coords=slice_x,
                               title="Similarity -sagittal", draw_cross=True, vmax=1)
    if slice_y != 0:
        plotting.plot_stat_map(stat_map_img=img, bg_img=background, display_mode='y', cut_coords=slice_y,
                               title="Similarity -coronal", draw_cross=True, vmax=1)
    if slice_z != 0:
        plotting.plot_stat_map(stat_map_img=img, bg_img=bg, display_mode='z', cut_coords=slice_z,
                               title="Similarity -axial", draw_cross=True, vmax=1)

    return 0

def plot_brainrsa_glass(img, threshold=None):

    if threshold != None:

        imgarray = nib.load(img).get_data()
        affine = get_affine(img)

        imgarray = correct_by_threshold(imgarray, threshold)

        img = nib.Nifti1Image(imgarray, affine)

    plotting.plot_glass_brain(img, colorbar=True, title="Similarity", black_bg=True, draw_cross=True, vmax=1)

    plt.show()

def plot_brainrsa_surface(img, threshold=None):

    if threshold != None:

        imgarray = nib.load(img).get_data()
        affine = get_affine(img)

        imgarray = correct_by_threshold(imgarray, threshold)

        img = nib.Nifti1Image(imgarray, affine)

    fsaverage = datasets.fetch_surf_fsaverage(mesh='fsaverage')
    texture_left = surface.vol_to_surf(img, fsaverage.pial_left)
    texture_right = surface.vol_to_surf(img, fsaverage.pial_right)
    plotting.plot_surf_stat_map(fsaverage.pial_left, texture_left, hemi='left', threshold=0.1,
                                bg_map=fsaverage.sulc_right, colorbar=True, vmax=1, darkness=0.7)
    plotting.plot_surf_stat_map(fsaverage.pial_right, texture_right, hemi='right', threshold=0.1,
                                bg_map=fsaverage.sulc_right, colorbar=True, vmax=1, darkness=0.7)
    plotting.plot_surf_stat_map(fsaverage.pial_left, texture_right, hemi='right', threshold=0.1,
                                bg_map=fsaverage.sulc_right, colorbar=True, vmax=1, darkness=0.7)
    plotting.plot_surf_stat_map(fsaverage.pial_right, texture_left, hemi='left', threshold=0.1,
                                bg_map=fsaverage.sulc_right, colorbar=True, vmax=1, darkness=0.7)

    plt.show()

def plot_brainrsa_rlts(img, threshold=None, slice=[6, 6, 6], background=None):

    if threshold != None:

        imgarray = nib.load(img).get_data()
        affine = get_affine(img)

        imgarray = correct_by_threshold(imgarray, threshold)

        img = nib.Nifti1Image(imgarray, affine)

    if background == None:

        plot_brainrsa_regions(img, threshold=threshold)

        plot_brainrsa_montage(img, threshold=threshold, slice=slice)

        plot_brainrsa_glass(img, threshold=threshold)

        plot_brainrsa_surface(img, threshold=threshold)

    else:

        plot_brainrsa_regions(img, threshold=threshold, background=background)

        plot_brainrsa_montage(img, threshold=threshold, slice=slice, background=background)

        plot_brainrsa_glass(img, threshold=threshold)
