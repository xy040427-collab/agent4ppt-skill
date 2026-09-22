"""Controlled raster mutations establish diagnostic sensitivity, not live QA."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/agent4ppt-skill/scripts'))
from PIL import Image, ImageDraw
from agent4ppt.comparison import measure


class RasterComparison(unittest.TestCase):
    def setUp(self):
        self.background=Image.new('RGB',(400,200),'white')
        self.overlay=[dict(id='title',text='TEST',x=.1,y=.1,w=.8,h=.6)]
        self.shapes={'title':dict(bounds=[.1,.1,.8,.6],runs=[])}

    def glyphs(self,dx=0,scale=1,color='navy'):
        image=self.background.copy();draw=ImageDraw.Draw(image)
        for x in (65,95,125,155):
            draw.rectangle((x+dx,45,x+dx+int(10*scale),45+int(25*scale)),fill=color)
        return image

    def result(self,image):
        return measure(self.glyphs(),self.background,image,self.overlay,self.shapes)[0]

    def test_identical_render_has_no_flags(self):
        self.assertEqual(self.result(self.glyphs())['flags'],[])

    def test_position_shift_detected(self):
        result=self.result(self.glyphs(dx=22))
        self.assertIn('position',result['flags'])
        self.assertEqual(result['metrics']['center_delta_px'],[22,0])

    def test_visible_size_change_detected(self):
        self.assertIn('visible_size_or_wrapping',self.result(self.glyphs(scale=1.6))['flags'])

    def test_color_change_detected(self):
        self.assertIn('color_or_emphasis',self.result(self.glyphs(color='orange'))['flags'])

    def test_missing_text_detected(self):
        self.assertIn('render_text_missing',self.result(self.background)['flags'])

    def test_lost_minority_emphasis_detected(self):
        target=self.glyphs();draw=ImageDraw.Draw(target)
        for x in (65,95):draw.rectangle((x,45,x+10,70),fill='orange')
        result=measure(target,self.background,self.glyphs(),self.overlay,self.shapes)[0]
        self.assertIn('color_or_emphasis',result['flags'])

    def test_measurement_contamination_not_approved(self):
        result=measure(Image.new('RGB',(400,200),'blue'),self.background,self.glyphs(),self.overlay,self.shapes)[0]
        self.assertIn('background_or_region_contamination',result['flags'])


if __name__=='__main__':unittest.main()
