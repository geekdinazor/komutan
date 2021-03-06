# -*- coding: utf-8 -*-
import os,time
import copy
import json
import socket
from flask import Flask,redirect,url_for,session
from flask import g
from flask import render_template #render yapmak icin
from flask import request 
from flask import Response
from arge import *
from random import randint
import codecs
import sqlite3 as sqlmak
import subprocess
from htmlrapor import *
import psutil

ag_bilgi_komut="ifconfig"#"nmcli con show"
arger=Arge()
KULL_ID=-1
SECRET_KEY = 'sds234fv'
uxterm_ayar=' -bg black -fg gray -fs 13 '
sanal_konsol_port="6061"

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def anaModul():
	if "KULL_ID" in session and arger.girdi_kontrol(session['KULL_ID']) :
			return render_template('anaModul.html')
	return redirect(url_for('giris'))

@app.route('/yonlendir/<moduladi>')
def yonlendir(moduladi):
	if "KULL_ID" in session and arger.girdi_kontrol(session['KULL_ID']) :
			return redirect(url_for(moduladi))	
	return redirect(url_for('giris') + "?" + moduladi)	
	
@app.route('/onkar')
def onkar():
	return "python-flask tabanli linux bilgi ve komut yonetim sunucusu- LKomutan"
	#return render_template('anasayfa.html')

@app.route('/cikis')
def cikis():
	arger.girdi_sil(session['KULL_ID'])
	session['KULL_ID']=-1
	return render_template('giris.html')
	
@app.route('/giris', methods=['GET', 'POST'])
def giris():
	error = None
	
	if request.method == 'POST':
		isim=request.form['username']
		sifre=request.form['password']
		onayson=arger.sifre_kontrol(isim,sifre)
		print "giris onayi:",onayson
		if(onayson):
			print isim,"girisi:"
			arger.girdi_ekle(isim)
			print isim,"onaylandi."
			session['KULL_ID']=isim
			return redirect(request.environ["QUERY_STRING"])
		else:
			return redirect("/")	
	return render_template('giris.html', error=error)

@app.route('/giris_eski', methods=['GET', 'POST'])
def giris_eski():
	error = None
	session["KULL_ID"]=-1
	if request.method == 'POST':
		isim=request.form['username']
		sifre=request.form['password']
		id=arger.girdi_no(isim,sifre)
		if(id):
			if arger.girdi_kontrol(id) is None:
				arger.girdi_ekle(id)
			session['KULL_ID']=id
			return render_template('anaModul.html')
	return render_template('giris.html', error=error)

@app.route('/komutaModul', methods=['GET', 'POST'])	
def komutaModul():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		dizin='komuta'
		calismalist=arger.dizin_cek(dizin="komuta")
		return render_template('komutaModul.html',mod=dizin,komutlar=calismalist,kayitmodu='w')	
	else:
		return redirect("/yonlendir/komutaModul")

@app.route('/mpsModul', methods=['GET', 'POST'])	
def mpsModul():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		dizin='/root/talimatname/genel'
		calismalist=arger.dizin_cek(dizin=dizin)
		yerel_ip=([(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1])
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			print s.connect((yerel_ip,int(sanal_konsol_port)))
		except socket.error, e:
			os.system("python3 butterfly/butterfly.server.py --unsecure --host=0.0.0.0 --port="+sanal_konsol_port)
		return render_template('mps.html',mod=dizin,komutlar=calismalist,kayitmodu='w',iframe="http://localhost:"+sanal_konsol_port+"/")	
	else:
		return redirect("/yonlendir/mpsModul")

@app.route('/mpsFaal', methods=['GET', 'POST'])
def mpsFaal():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		print request.args
		data="bos"
		if 'faal' in request.args:
			faal = request.args.get('faal')
			paket=request.form["paketara"]
			print paket
			if faal=="kur":
				if paket!="":
					#os.system('uxterm '+uxterm_ayar+' -e "mps -kur '+paket+' && sleep 3 && exit" ') 
					#os.system("killall uxterm")
					#isletilecek komut
					iskomut="mps kur "+paket
					os.system('python3 butterfly/butterfly.server.py --unsecure --one_shot --cmd="'+iskomut+'"')
					data="kuruluyor"
				else:
					data="boş paket"
				
			if faal=="sil":
				if paket!="":
					#os.system('uxterm '+uxterm_ayar+' -e "mps -s '+paket+' && sleep 3 && exit" ') 
					#os.system("killall uxterm")
					iskomut="mps sil "+paket
					os.system('python3 butterfly/butterfly.server.py --unsecure --one_shot --cmd="'+iskomut+'"')
					data="siliniyor"
				else:
					data="boş paket"
		else:
			data="parametre eksik"
		return Response(json.dumps(data),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")	

@app.route('/kurulum', methods=['GET', 'POST'])	
def kurulum():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		diskler=[]
		disklerdos=""
		os.system("ls /dev/sd* > kondarma/diskler")
		disklerdos=open("kondarma/diskler","r").read()
		diskler=disklerdos.split()
		#ornek data
		#diskler=["/dev/sdk","/dev/sdl"]
		return render_template('kurulum.html',diskler=diskler)	
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")

@app.route('/diskbilgi', methods=['GET', 'POST'])
def diskbilgi():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		data=""
		disk=request.form["kurdisk"]
		os.system("df -h | grep "+str(disk)+" > kondarma/diskbilgi")
		diskbilgi=open("kondarma/diskbilgi","r").read()
		data+=diskbilgi
		return Response(json.dumps(data),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")	

@app.route('/disksil_islem', methods=['GET', 'POST'])
def disksil_islem():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		data=""
		disk=request.form["kurdisk"]
		#disk silinir.
		data="tamam"
		return Response(json.dumps(data),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")	

@app.route('/diskkur_islem', methods=['GET', 'POST'])
def diskkur_islem():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		#kurulum_komut="cp -axvnu /  /mnt"
		kurulum_komut="echo 'kurulum' "  
		os.system('uxterm '+uxterm_ayar+' -e "'+kurulum_komut+' && sleep 3 && exit" ') 
		#os.system("killall uxterm")
		data="tamam"
		return Response(json.dumps(data),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")	
		
@app.route('/diskbol_islem', methods=['GET', 'POST'])
def diskbol_islem():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		#ilgili bolumleme programı açılır.
		os.system("gparted") 
		data="tamam"
		return Response(json.dumps(data),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")
		
@app.route('/diskbagla_islem', methods=['GET', 'POST'])
def diskbagla_islem():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		data=""
		disk=request.form["kurdisk"]
		data="tamam"
		return Response(json.dumps(data),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")	

@app.route('/kull_islem', methods=['GET', 'POST'])
def kull_islem():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		kull_komut="ko"  
		os.system('uxterm '+uxterm_ayar+' -e "'+kull_komut+' && sleep 3 && exit" ') 
		#os.system("killall uxterm")
		data="tamam"
		return Response(json.dumps(data),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")	

@app.route('/paketlist', methods=['GET', 'POST'])
def paketlist():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		data=os.listdir("/root/talimatname/genel")
		lst = []
		for pn in data:
			d = {}
			d['isim']=pn
			lst.append(d)
		if lst:
			return Response(json.dumps(lst),mimetype='application/json')
		else:
			return Response(json.dumps("hata"),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")	

@app.route('/paketDurum', methods=['GET', 'POST'])
def paketdurum():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		data="yok"
		paket=request.form["paketara"]
		if paket!="":
			os.system("mps -kk "+paket+" > kondarma/paketdurum.log")
			kk=open("kondarma/paketdurum.log","r").read()
			print "--",kk
			if "kurulu" in kk:
				data="tamam"
		else:
			data="paket tanımsız"
		
		return Response(json.dumps(data),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")	


@app.route('/surecModul', methods=['GET', 'POST'])	
def surecModul():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		surecler=arger.komut_kos("netstat -natpl","sh")
		surecler=surecler.split("\n")
		'''rapor="<html><table  border=1  align=left>"
		for surec in surecler:
			if "Active" not in surec and "Proto" not in surec: 
				rapor+="<tr>"
				for sur in surec.split():
					rapor+="<td>"+sur+"</td>"
				rapor+="</tr>"
		rapor+="</table></html>"'''
		rapor=statikrapor()
		dizibas=[]
		top_sutlar=[]
		rapor_html=rapor.diziYhtml2(surecler,dizibas,top_sutlar)
		rapor=rapor_html
		return render_template('surecModul.html')+rapor
	else:
		return redirect("/yonlendir/surecModul")
		
@app.route('/arayuzModul', methods=['GET', 'POST'])	
def arayuzModul():
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		dizin='templates'
		arayuzlist=arger.dizin_cek(dizin="templates")
		return render_template('arayuzModul.html',mod=dizin,arayuzler=arayuzlist,kayitmodu='w')	
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")	
		
@app.route('/komutanGuncelle', methods=['GET', 'POST'])	
def komutanGuncelle():
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		os.system("git pull > kondarma/guncelleme.log")
		log=open("kondarma/guncelleme.log","r").read()
		return "<html>güncellendi:<p>"+log+"<p><a href='/'>ana sayfa</a> </html>"
	else:
		return redirect("/yonlendir/komutanGuncelle")

@app.route('/komutCalistir', methods=['GET', 'POST'])
def komutCalistir():
	onay=1
	if(onay==1):
		komut=request.form["calismakod"]
		komutson=""
		onkomut=""
		komutdos=request.form["calismalist"]
		if ".sh" in komutdos:
			komut=komut.split("\n")
			for kom in komut:
				komek=kom
				if '=' in kom and 'if ' not in kom:
					baslik=kom.split('=')[0]
					deger=kom.split('=')[1]
					ydeger=request.form[baslik]
					komek=baslik+"="+str(ydeger)
				komutson+=komek+"\n"
			onkomut=""
		else:
			komutson=komut
		if "#python" in komut:
			onkomut="python "
		
		sonuc=arger.komut_kos(komutson,onkomut)
		return Response(json.dumps(sonuc),mimetype='application/json')
	else:		
		return render_template('giris.html', error="isim ve sifre giriniz")

@app.route('/calismaAl', methods=['GET', 'POST'])
def komutAl():
	onay=1
	if(onay==1):
		if('mod' in request.args):
			dizin = request.args.get('mod')
		else:
			dizin='komuta'
		if('dosya' in request.args):
			dosya = request.args.get('dosya')
		else:
			dosya='test.sh'
		try:
			data=codecs.open(dizin+"/"+dosya,"r").read()
			return Response(json.dumps(data),mimetype='application/json')
		except:
			return Response(json.dumps("hata"),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")


@app.route('/calismaKaydet', methods=['GET', 'POST'])
def calismaKaydet():
	onay=1
	if(onay==1):
		kayitmodu = request.form['kayitmodu']
		komut = request.form['calismakod']
		if(kayitmodu=='w'):
			dosya = request.form['yenicalisma']
		else:
			dosya = request.form['calismalist']
		dizin = request.form['mod']
		test=codecs.open(dizin+"/"+dosya,"w","utf-8").write(komut)
		sonuc="tamam"
		return Response(json.dumps(sonuc),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")
	
@app.route('/agModul')
def agModul():
	
	return render_template('ag.html')
	
@app.route('/arayuzModul_eski', methods=['GET', 'POST'])
def arayuzModul_eski():
	onay=1
	if(onay==1):
		html="<html>"
		komutdos = request.args.get('kd')#"komuta/paket_kur.sh"
		komut=codecs.open("komuta/"+komutdos,"r",'utf-8').read()
		komut=komut.split("\n")
		html+=komutdos+"<p>"
		for kom in komut:
			if '=' in kom and 'if' not in kom:
				deger=kom.split('=')[1]
				deguz=len(kom.split('=')[1])*8+10
				html+=kom.split('=')[0]+":"+"<input type=text id="+kom.split('=')[0]+" name="+kom.split('=')[0]+"  value="+deger+" tabindex='-1' style='width:"+str(deguz)+"px;'/>"+"<br>"
		html+="<p>"+"<input type='submit' name='calistir' id='calistir' value='betik_kos' tabindex='-1'/>"+"<p>"
		html+="<a href='/'><img src='/static/ana.png' class='hover' hinttext='anasayfa' style='margin-right:120px;'></a>" 
		html+="<a href='/komutaModul'><img src='/static/komuta.png' class='hover' hinttext='komuta' style='margin-right:120px;'></a>" 
		html+=""+"</html>"
		return html
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")

@app.route('/ag_bilgi', methods=['GET', 'POST'])
def ag_bilgi():
	onay=1
	if(onay==1):
		#rapor="AG BILGILERI<br>"
		fname="agModul.kom"
		komutsan=""
		rapor="<html>"
		with open(fname) as f:
			ag_komutdos = f.readlines()
		for komutdos in ag_komutdos:
			komutson="<strong>"+komutdos.strip()+"</strong><br>"+arger.komut_doskos(komutdos.strip())
			rapor+=komutson+"<br>"
		rapor+="</html>"
		return Response(json.dumps(rapor),mimetype='application/json')
	return render_template('giris.html', error="isim ve sifre giriniz")

if __name__ == '__main__':
	host="0.0.0.0"
	port_calis=6060
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		sock.connect_ex((host,port_calis))
		app.run(host=host,port=port_calis,debug=True,use_evalex=True,threaded=True) 
	except Exception, e:
		if "Errno 98" in str(e):
			print "Komutan zaten çalışıyor.Port kullanımda."
