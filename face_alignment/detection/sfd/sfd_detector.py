import torch
from torch.utils.model_zoo import load_url

from ..core import FaceDetector

from .net_s3fd import s3fd
from .bbox import nms
from .detect import detect, batch_detect

try:
    from torch.hub import get_dir
except BaseException:
    from torch.hub import _get_torch_home as get_dir
import os

models_urls = {
    's3fd': 'local_models/sfd/s3fd-619a316812.pth',
}


class SFDDetector(FaceDetector):
    '''SF3D Detector.
    '''

    def __init__(self, device, path_to_detector=None, verbose=False, filter_threshold=0.5):
        super(SFDDetector, self).__init__(device, verbose)

        # Initialise the face detector
        if path_to_detector is None:
            hub_dir = os.path.abspath(os.getcwd())
            model_path = os.path.join(hub_dir, models_urls['s3fd'])
            model_weights = torch.load(model_path)
        else:
            model_weights = torch.load(path_to_detector)

        self.fiter_threshold = filter_threshold
        self.face_detector = s3fd()
        self.face_detector.load_state_dict(model_weights)
        self.face_detector.to(device)
        self.face_detector.eval()

    def _filter_bboxes(self, bboxlist):
        if len(bboxlist) > 0:
            keep = nms(bboxlist, 0.3)
            bboxlist = bboxlist[keep, :]
            bboxlist = [x for x in bboxlist if x[-1] > self.fiter_threshold]

        return bboxlist

    def detect_from_image(self, tensor_or_path):
        image = self.tensor_or_path_to_ndarray(tensor_or_path)

        bboxlist = detect(self.face_detector, image, device=self.device)[0]
        bboxlist = self._filter_bboxes(bboxlist)

        return bboxlist

    def detect_from_batch(self, tensor):
        bboxlists = batch_detect(self.face_detector, tensor, device=self.device)

        new_bboxlists = []
        for i in range(bboxlists.shape[0]):
            bboxlist = bboxlists[i]
            bboxlist = self._filter_bboxes(bboxlist)
            new_bboxlists.append(bboxlist)

        return new_bboxlists

    @property
    def reference_scale(self):
        return 195

    @property
    def reference_x_shift(self):
        return 0

    @property
    def reference_y_shift(self):
        return 0
