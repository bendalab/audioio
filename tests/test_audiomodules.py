import pytest
import numpy as np
import audioio.audiomodules as am


def test_audiomodules():
    am.enable_module()
    funcs = ['all', 'fileio', 'device']
    for func in funcs:
        am.enable_module()
        print('')
        print('module lists for %s:' % func)
        inst_mods = am.installed_modules(func)
        print('installed:', len(inst_mods), inst_mods)
        assert len(inst_mods) > 0, 'no installed modules for %s' % func
        avail_mods = am.available_modules(func)
        print('available:', len(avail_mods), avail_mods)
        assert len(avail_mods) == len(inst_mods), 'less available modules than installed modules for %s' % func
        unavail_mods = am.unavailable_modules(func)
        print('unavailable:', len(unavail_mods), unavail_mods)
        assert len(unavail_mods) >= 0, 'wrong number of unavailable modules for %s' % func
        missing_mods = am.missing_modules(func)
        print('missing:', len(missing_mods), missing_mods)
        assert len(missing_mods) >= 0, 'wrong number of missing modules for %s' % func
        am.missing_modules_instructions(func)
        am.list_modules(func, False)
        am.list_modules(func, True)

    print()
    print('single module functions:')
    for module in am.audio_modules.keys():
        am.disable_module(module)
        am.enable_module(module)
        am.select_module(module)
        am.enable_module()
        inst = am.installation_instruction(module)
        assert len(inst) > 0, 'no installation instructions for module %s' % module
        am.list_modules(module, False)
        am.list_modules(module, True)


def test_main():
    am.enable_module()
    am.main()
    for module in am.audio_modules.keys():
        am.main(module)
    
