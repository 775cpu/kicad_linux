#  U.cd('C:/Program Files/KiCad/10.0/bin/')
#  !python -m pip install dill flask KicadModTree
# __import__('ctypes').windll.user32.MessageBoxW(0, f'v10', 'title', 0)
import sys;'qgb.U' in sys.modules or sys.path.append(r'C:\QGB\anaconda3\Lib\site-packages\pythonwin');
import sys;'qgb.U' in sys.modules or sys.path.append(r'C:\QGB\miniforge3\Lib\site-packages\pythonwin');
from qgb import py
U,T,N,F=py.importUTNF()
import qgb.N.HTML

# for i in range(2233,9999):
    # if N.is_port_open(i):continue
    # else:    
        # N.rpcServer(globals=globals(),locals=locals(),port=i,no_banner=1,currentThread=0)  

try:
    N.rpcServer(globals=globals(),locals=locals(),port=2233,no_banner=1,currentThread=0)  
    from qgb import kicad
except Exception as e:
	kicad=e

try:import Q
except Exception as e:
	Q=e	

try:import q2026
except Exception as e:q2026=e
	
import Q,kicad	
	
# def loop():
	# U.sleep(5)
	# U.msgbox(__file__)
	# while(1):
		# U.set(0,U.stime())
		# U.sleep(1)
		
# U.Thread(target=loop).start()



import pcbnew
import re
import datetime


class text_by_date( pcbnew.ActionPlugin ):
	"""
	test_by_date: A sample plugin as an example of ActionPlugin
	Add the date to any text field of the board where the content is '$date$'
	How to use:
	- Add a text on your board with the content '$date$'
	- Call the plugin
	- Automatically the date will be added to the text (format YYYY-MM-DD)
	"""

	def defaults( self ):
		"""
		Method defaults must be redefined
		self.name should be the menu label to use
		self.category should be the category (not yet used)
		self.description should be a comprehensive description
		  of the plugin
		"""
		self.name = "Add date on PCB"
		self.category = "Modify PCB"
		self.description = "Automatically add date on an existing PCB"

	def Run( self ):
		pcb = pcbnew.GetBoard()
		for draw in pcb.GetDrawings():
			if draw.GetClass() == 'PTEXT':
				txt = re.sub( "\$date\$ [0-9]{4}-[0-9]{2}-[0-9]{2}",
								 "$date$", draw.GetText() )
				# U.msgbox(txt)
				if txt == "$date$":
					draw.SetText( "$date$ %s"%U.stime() )


text_by_date().register()
