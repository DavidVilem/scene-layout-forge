import unittest
from scene_model import make_part,validate
from connected_plant import fixture


class AccessGeometryTests(unittest.TestCase):
    def scene(self,reverse=False,kind='stair'):
        return {'units':'m','parts':[
            make_part('access',kind,[0,0,0],[1,3,2],parameters={'steps':10,'reverse':reverse}),
            make_part('deck','landing',[0,-1 if reverse else 3,1.8],[2,1,.2])],
            'stair_access' if kind=='stair' else 'ramp_access':[{kind:'access','landing':'deck'}]}

    def rail(self,start,end,height=1):
        return make_part('rail','railing',[10,10,0],[1,.1,height],parameters={'start':start,'end':end})

    def test_rejects_crossbar_for_forward_reverse_and_ramp(self):
        for reverse,kind in [(False,'stair'),(True,'stair'),(True,'ramp')]:
            with self.subTest(reverse=reverse,kind=kind):
                data=self.scene(reverse,kind);edge=0 if reverse else 3
                self.assertEqual(validate(data),[])
                data['parts'].append(self.rail([0,edge,2],[1,edge,2]))
                self.assertTrue(any('entrance blocked' in e for e in validate(data)))

    def test_side_rails_and_distant_rails_do_not_block(self):
        for start,end in [([0,3,2],[0,4,2]),([1,3,2],[1,4,2]),
                          ([0,4,2],[1,4,2]),([0,3,-1],[1,3,-1]),
                          ([0,3,4],[1,3,4])]:
            data=self.scene();data['parts'].append(self.rail(start,end))
            self.assertEqual(validate(data),[])

    def test_post_blocks_even_when_horizontal_bars_are_overhead(self):
        data=self.scene();data['parts'].append(self.rail([.5,3,2],[.5,4,2],height=5))
        self.assertTrue(any('entrance blocked' in e for e in validate(data)))

    def test_existing_connected_plant_has_open_entrance(self):
        self.assertEqual(validate(fixture()),[])


if __name__=='__main__':unittest.main()
