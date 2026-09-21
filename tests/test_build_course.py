import unittest,tempfile,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build_course import compose,build,ROOT
class CourseBuildTests(unittest.TestCase):
 def test_course_sources_compose(self):
  page=compose()
  for anchor in ['engram-script','engram-part-5','engram-paper','engram-code']:
   self.assertIn('id=\"'+anchor+'\"',page)
  self.assertNotIn('<!-- include:',page)
 def test_cycle_and_saved_edit_protection(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'index.template.html').write_text('<!-- include: nested.html -->');(p/'nested.html').write_text('<!-- include: index.template.html -->')
   with self.assertRaisesRegex(ValueError,'Circular'):compose(p)
   (p/'nested.html').write_text('<p data-edit-id="one">a</p>');(p/'content').mkdir();(p/'content/text-edits.json').write_text(json.dumps({'edits':{'lost':'Keep me'}}))
   with self.assertRaisesRegex(ValueError,'orphaned'):compose(p)
 def test_build_updates_after_source_change(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'index.template.html').write_text('<!-- include: lesson.html -->');(p/'lesson.html').write_text('First');build(p)
   (p/'lesson.html').write_text('Revised');build(p);self.assertEqual((p/'index.html').read_text(),'Revised')
 def test_duplicate_ids_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'index.template.html').write_text('<p data-edit-id="same"></p><p data-edit-id="same"></p>')
   with self.assertRaisesRegex(ValueError,'Duplicate'):compose(p)
if __name__=='__main__':unittest.main()
