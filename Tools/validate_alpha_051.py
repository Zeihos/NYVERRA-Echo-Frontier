"""Offline project integrity checks; not a substitute for Unreal compilation."""
from pathlib import Path
import json
import unittest
from summarize_build_051 import summarize

ROOT = Path(__file__).resolve().parents[1]

class Alpha051Checks(unittest.TestCase):
    def test_project_configuration(self):
        config = json.loads((ROOT/'NYVERRA.uproject').read_text(encoding='utf-8'))
        self.assertEqual(config['EngineAssociation'], '5.8')
        self.assertIn('NYVERRA', [x['Name'] for x in config['Modules']])

    def test_targets_exist(self):
        for file in ('Source/NYVERRAEditor.Target.cs', 'Source/NYVERRA.Target.cs', 'Source/NYVERRAServer.Target.cs', 'Source/NYVERRA/NYVERRA.Build.cs'):
            with self.subTest(file=file):
                self.assertTrue((ROOT/file).is_file())

    def test_build_script(self):
        body = (ROOT/'BUILD_ALPHA_051_WINDOWS.bat').read_text()
        self.assertIn('NYVERRAEditor Win64 Development', body)
        self.assertIn('BUILD_ALPHA_051_ERRORS.txt', body)
        self.assertIn('exit /b !RESULT!', body)

    def test_extract_cxx_errors(self):
        log = 'compiling...\nNyCharacter.cpp(17): error C2065: test: undeclared identifier\nwarning C4100 ignored\n'
        self.assertIn('error C2065', summarize(log))
        self.assertNotIn('warning C4100', summarize(log))

    def test_required_source(self):
        for file in ('NyCharacter', 'NyEnemy', 'NyResource', 'NyGameMode', 'NyWorldState'):
            with self.subTest(file=file):
                self.assertTrue((ROOT/f'Source/NYVERRA/Private/{file}.cpp').exists())
                self.assertTrue((ROOT/f'Source/NYVERRA/Public/{file}.h').exists())

if __name__ == '__main__':
    unittest.main(verbosity=2)
