import sys,unittest,tempfile,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/agent4ppt-skill/scripts'))
from agent4ppt.layout import reserved_regions,layout_issues,write_layout_guide
from agent4ppt.plan import validate,compile_request
from PIL import Image

class Layout(unittest.TestCase):
    def page(self):
        return dict(title='Title',overlays=[dict(id='title',type='text',text='Title',x=.1,y=.1,w=.8,h=.1,safe_padding=.02)])

    def test_padding_has_same_physical_size_in_both_directions(self):
        r=reserved_regions(self.page())[0]
        self.assertAlmostEqual((.1-r['x'])*1600,(.1-r['y'])*900)
        self.assertEqual(r['policy'],'quiet')

    def test_bounds_intersection_is_reported(self):
        p=self.page();p['overlays'].append(dict(id='body',x=.2,y=.15,w=.2,h=.2))
        self.assertEqual(layout_issues(p)[0]['objects'],['title','body'])

    def test_bad_padding_rejected_before_request(self):
        for value in [-.1,float('nan'),'large',True]:
            p=self.page();p['overlays'][0]['safe_padding']=value
            with self.assertRaises(ValueError):validate(dict(title='D',mode='editable',pages=[p]),'.')

    def test_guide_pixels_and_reservations_reach_request(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.page();ref=write_layout_guide(p,Path(d)/'guide.png');p['references']=[ref]
            brief=validate(dict(title='D',mode='editable',editable_workflow='reserved',review_policy='structured-v1',pages=[p]),d)
            request=compile_request(brief,brief['pages'][0])
            self.assertEqual(request['review_policy'],'structured-v1')
            self.assertEqual(len(request['references']),1)
            self.assertIn('Native overlay safety regions',request['prompt'])
            with Image.open(ref['path']) as im:
                self.assertEqual(im.size,(1600,900))
                self.assertEqual(im.getpixel((200,130)),(255,241,247))
                self.assertEqual(im.getpixel((800,500)),(255,255,255))

    def test_review_policy_typo_rejected(self):
        with self.assertRaises(ValueError):validate(dict(title='D',mode='editable',review_policy='strctured',pages=[self.page()]),'.')

if __name__=='__main__':unittest.main()
