"""Own pin facts: schematic FMC contact -> board net -> FPGA -> SRAM TSOP.

Not a copy of the vendor XDC. The optional original-file check is read-only;
published evidence contains facts/hashes, never the restricted source file.
"""
import argparse,hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
MASTER_HASH='4c3ae9d40dce0cb0ca86fdd381a3ec05e0cc099c6f17f8299e270690b2b58b5c'
# Checked against ZedBoard schematic D.2 sheet2 and Master XDC.
# Tuple per pair: (positive connector contact, negative connector contact).
CONTACTS={0:('G6','G7'),1:('D8','D9'),2:('H7','H8'),3:('G9','G10'),
 4:('H10','H11'),5:('D11','D12'),6:('C10','C11'),7:('H13','H14'),
 8:('G12','G13'),9:('D14','D15'),17:('D20','D21'),18:('C22','C23'),
 19:('H22','H23'),20:('G21','G22'),21:('H25','H26'),22:('G24','G25'),
 23:('D23','D24'),24:('H28','H29'),25:('G27','G28'),26:('D26','D27'),
 27:('C26','C27'),32:('H37','H38')}
PINS={0:('M19','M20'),1:('N19','N20'),2:('P17','P18'),3:('N22','P22'),
 4:('M21','M22'),5:('J18','K18'),6:('L21','L22'),7:('T16','T17'),
 8:('J21','J22'),9:('R20','R21'),17:('B19','B20'),18:('D20','C20'),
 19:('G15','G16'),20:('G20','G21'),21:('E19','E20'),22:('G19','F19'),
 23:('E15','D15'),24:('A18','A19'),25:('D22','C22'),26:('F18','E18'),
 27:('E21','D21'),32:('A21','A22')}
SRAM_A=[25,24,23,22,21,20,19,18,8,7,6,5,4,3,2,1,48,17,16,9]
SRAM_DQ=[29,31,33,35,38,40,42,44,30,32,34,36,39,41,43,45]

def plan():
    rows=[]
    def add(port,la,negative,pin):
        side='N' if negative else 'P';cc='_CC' if la in [0,1,17,18] else ''
        rows.append({'port':port,'FPGA_pin':PINS[la][int(negative)],'FMC_net':f'FMC_LA{la:02}{cc}_{side}',
          'FMC_contact':CONTACTS[la][int(negative)],'bank':34 if la<17 else 35,'SRAM_TSOP48_pin':pin,
          'standard':'LVCMOS33','VADJ_V':3.3})
    add('sram_a[0]',32,True,SRAM_A[0])
    for i in range(1,20):add(f'sram_a[{i}]',i//2,i%2==0,SRAM_A[i])
    for i in range(16):add(f'sram_dq[{i}]',17+i//2,i%2==0,SRAM_DQ[i])
    for i,(port,pin) in enumerate([('sram_ce_n',26),('sram_oe_n',28),('sram_we_n',11),
                                   ('sram_lb_n',15),('sram_ub_n',14),('sram_err',13)]):
        add(port,25+i//2,i%2==0,pin)
    return rows

def validate(rows,xdc,io):
    assert len(rows)==42
    for key in ['port','FPGA_pin','FMC_contact','SRAM_TSOP48_pin']:assert len({x[key] for x in rows})==42,key
    assert {x['SRAM_TSOP48_pin'] for x in rows}|{10,12,27,37,46,47}==set(range(1,49))
    assignments={port:pin for pin,port in re.findall(r'set_property PACKAGE_PIN (\w+) \[get_ports \{([^}]+)\}\]',xdc)}
    iomap={}
    for line in io.splitlines():
        cols=[c.strip() for c in line.split('|')]
        if len(cols)>12 and cols[2].startswith('sram_'):iomap[cols[2]]=cols
    for row in rows:
        assert assignments[row['port']]==row['FPGA_pin'],row
        c=iomap[row['port']]
        assert c[1]==row['FPGA_pin'] and c[6]=='LVCMOS33' and int(c[7])==row['bank'],row
    assert 'set_property PACKAGE_PIN Y9 [get_ports ref100]' in xdc

def main():
    p=argparse.ArgumentParser();p.add_argument('route',type=Path);p.add_argument('--master-xdc',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    rows=plan();xdc=(HERE/'board_pins.xdc').read_text();io=(a.route/'io.rpt').read_text()
    validate(rows,xdc,io)
    mutant=[dict(x) for x in rows];mutant[1]['FPGA_pin']=mutant[0]['FPGA_pin']
    try:validate(mutant,xdc,io)
    except AssertionError:pass
    else:raise AssertionError('duplicate-pin mutant accepted')
    if a.master_xdc:
        data=a.master_xdc.read_bytes();assert hashlib.sha256(data).hexdigest()==MASTER_HASH
        facts={net:pin for pin,net in re.findall(rb'PACKAGE_PIN (\w+) \[get_ports \{(FMC_LA[^}]+)\}\]',data)}
        for row in rows:assert facts[row['FMC_net'].encode()].decode()==row['FPGA_pin']
    r={'scope':'proposed adapter, independently checked pin facts, not manufactured wiring',
       'rows':rows,'ref100':{'pin':'Y9','source':'HW UG v2.2 section2.5 p18, IC17 Fox767-100-136',
          'nominal_MHz':100,'frequency_span_qualification':'project condition, not established for stock oscillator'},
       'straps':{'SRAM_CE2_pin12':'VCC','SRAM_BYTE_pin47':'VCC selects x16',
                 'SRAM_VCC_pin37':'3.3V common rail','SRAM_VSS_pins27_46':'GND','SRAM_NC_pin10':'unconnected',
                 'note':'pin45 is DQ15 in x16 and A20 in x8; not the BYTE strap'},
       'master_XDC_SHA256':MASTER_HASH,'master_reread':bool(a.master_xdc),
       'source_urls':['https://raw.githubusercontent.com/Digilent/digilent-xdc/master/Zedboard-Master.xdc',
                      'https://digilent.com/reference/_media/reference/programmable-logic/zedboard/zedboard_sch.pdf'],
       'xdc_SHA256':hashlib.sha256(xdc.encode()).hexdigest(),'io_report_SHA256':hashlib.sha256(io.encode()).hexdigest(),
       'duplicate_pin_mutant_rejected':True}
    s=json.dumps(r,indent=2)+'\n'
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(s)
    print(s)
if __name__=='__main__':main()
