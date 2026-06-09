#!/usr/bin/env python3
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, 'dist')
WDOCDIR = os.path.join(os.path.dirname(ROOT), 'wdoc')

htmlfiles = ['index_s.htm.gz','control_s.htm.gz','config.htm.gz','setup.htm.gz','logging.htm.gz','gravity.htm.gz','gravity_e32.htm.gz','pressure.htm.gz','backup.htm.gz']
variables = ['data_index_htm_gz','control_htm_gz','config_htm_gz','setup_htm_gz','logging_htm_gz','gravity_htm_gz','gravity_e32_htm_gz','pressure_htm_gz','backup_htm_gz']
outfiles = ['index_htm','control_htm','config_htm','setup_htm','log_htm','gdc_htm','gdc_e32_htm','pressure_htm','backup_htm']
languages = ['norwegian','english','spanish','portuguese-br','slovak','chinese','italian']

if not os.path.isdir(WDOCDIR):
    print('wdoc directory not found at', WDOCDIR)
    sys.exit(2)

for lang in languages:
    for idx, h in enumerate(htmlfiles):
        src = os.path.join(DIST, lang, h)
        if not os.path.isfile(src):
            print('missing', src)
            continue
        outname = f"{lang}_{outfiles[idx]}.h"
        outpath = os.path.join(WDOCDIR, outname)
        var = variables[idx]
        # read bytes
        with open(src, 'rb') as f:
            data = f.read()
        # write header
        with open(outpath, 'w', encoding='utf-8') as fh:
            fh.write('const unsigned char %s[] PROGMEM = {' % var)
            # write bytes in hex
            line = []
            for i, b in enumerate(data):
                line.append('0x%02x' % b)
                if len(line) >= 12:
                    fh.write('\n')
                    fh.write('  ' + ', '.join(line) + ',')
                    line = []
                else:
                    fh.write(' ' + ('0x%02x,' % b))
            if line:
                fh.write('\n  ' + ', '.join(line) + ',\n')
            fh.write('\n};\n')
            fh.write('unsigned int %s_len = %d;\n' % (var, len(data)))
        print('wrote', outpath)

print('done')
