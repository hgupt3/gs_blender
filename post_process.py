import os
import numpy as np
import cv2
import shutil

root_dir = os.environ.get('GELSIGHT_RENDER_DIR', os.path.join(os.path.dirname(__file__), 'renders'))


def dmap2norm(dmap):
    zx = cv2.Sobel(dmap, cv2.CV_64F, 1, 0, ksize=5)
    zy = cv2.Sobel(dmap, cv2.CV_64F, 0, 1, ksize=5)

    normals = np.dstack((-zx, -zy, np.ones_like(dmap)))
    length = np.linalg.norm(normals, axis=2)
    length = length[:, :, np.newaxis]
    normals[:, :, :] /= length

    normals += 1
    normals /= 2
    return normals[:, :, ::-1].astype(np.float32)


sensors = os.listdir(root_dir)
for sensor in sensors:
    change_dir = os.path.join(root_dir, sensor)
    raw_depth_dir = os.path.join(change_dir, 'raw_data')
    dmaps_dir = os.path.join(change_dir, 'dmaps')
    norms_dir = os.path.join(change_dir, 'norms')

    if os.path.exists(norms_dir) == True:
        shutil.rmtree(norms_dir)
    if os.path.exists(dmaps_dir) == True:
        shutil.rmtree(dmaps_dir)
    os.mkdir(norms_dir)
    os.mkdir(dmaps_dir)

    raw_depths = os.listdir(raw_depth_dir)
    raw_depths.sort()

    for raw in raw_depths:
        raw_dir = os.path.join(raw_depth_dir, raw)
        dmap_dir = os.path.join(dmaps_dir, raw[0:4] + '.png')
        norm_dir = os.path.join(norms_dir, raw[0:4] + '.png')

        raw = np.load(raw_dir)

        norm = dmap2norm(raw)
        norm = np.clip(norm, 0, 1)
        norm = (norm * 255).astype(np.uint8)
        cv2.imwrite(norm_dir, norm)

        dmap = np.clip(raw, 0, 1)
        dmap = (dmap * 255).astype(np.uint8)
        cv2.imwrite(dmap_dir, dmap)


