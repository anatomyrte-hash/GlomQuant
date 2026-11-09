"""Meaningful frozen filter boundary and ordering checks; no model download."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['LOCALAPPDATA']=str(Path(tempfile.gettempdir())/'glomquant_engine_tests')
from app import extra_filter
from infer_wsi_pilot import global_nms,starts

def box(x1,y1,x2,y2,confidence):
    return dict(x1=x1,y1=y1,x2=x2,y2=y2,width=x2-x1,height=y2-y1,confidence=confidence)

class FrozenEngine(unittest.TestCase):
    def test_half_overlap_is_retained(self):
        kept,audit=extra_filter([box(0,0,10,10,.9),box(5,0,15,10,.8)])
        self.assertEqual(len(kept),2);self.assertEqual(audit,[])

    def test_contained_partial_box_removed_by_smaller_area(self):
        # Low IoU alone misses this duplicate; the established extra filter removes it.
        detections=[box(0,0,100,100,.9),box(10,10,20,20,.8)]
        merged=global_nms(detections,.5)
        self.assertEqual(len(merged),2)
        kept,audit=extra_filter(merged)
        self.assertEqual([b['detection_id'] for b in kept],[1])
        self.assertEqual(audit[0]['removed_id'],2)

    def test_tied_confidence_preserves_first_id(self):
        kept,audit=extra_filter([box(0,0,10,10,.8),box(0,0,10,10,.8)])
        self.assertEqual([b['detection_id'] for b in kept],[1])

    def test_empty_result_is_valid(self):
        self.assertEqual(extra_filter([]),([],[]));self.assertEqual(global_nms([]),[])

    def test_grid_retains_last_edge(self):
        self.assertEqual(starts(2000,1024,768),[0,768,976])
        self.assertEqual(starts(500,1024,768),[0])

if __name__=='__main__':unittest.main()
