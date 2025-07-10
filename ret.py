# -*- coding: utf-8 -*-
"""
Created on Wed Jun 4 17:44:05 2025

@author: Victus
"""

import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from datetime import datetime
from PyQt5.QtCore import QDate
import os

# ui dosyalarınızın importları
from proui import Ui_makul
from geziui import Ui_magezi
def clean_sqlite_temp_files(db_path):
    """
    Belirtilen SQLite veritabanı dosyasının etrafındaki geçici dosyaları (journal, wal, shm vb.) temizler.
    """
    # Veritabanı dosyasının tam yolunu kontrol et
    if not os.path.isabs(db_path):
        # Eğer db_path sadece dosya adı ise, mevcut çalışma dizinini kullan
        db_dir = os.getcwd()
        full_db_path = os.path.join(db_dir, db_path)
    else:
        # Eğer db_path tam bir yol ise, dizinini al
        db_dir = os.path.dirname(db_path)
        full_db_path = db_path

    db_name_base = os.path.basename(full_db_path) # sehir.db
    # '.db' uzantısını kaldırarak temel ismi al (örneğin 'sehir')
    if db_name_base.endswith('.db'):
        base_name_without_ext = db_name_base[:-3]
    else:
        base_name_without_ext = db_name_base

    # Olası geçici dosya uzantıları
    temp_extensions = ['.db-journal', '.db-wal', '.db-shm', '.db-bak', '.sqlite-journal', '.sqlite-wal', '.sqlite-shm']

    print(f"'{full_db_path}' için geçici SQLite dosyaları kontrol ediliyor. Dizinde: '{db_dir}'")

    deleted_files = []
    try:
        # Dizin mevcut ve erişilebilir mi kontrol et
        if not os.path.exists(db_dir) or not os.path.isdir(db_dir):
            print(f"Uyarı: Dizin bulunamadı veya erişilemiyor: '{db_dir}'. Geçici dosyalar temizlenemedi.")
            return

        for filename in os.listdir(db_dir):
            # Dosya adının veritabanı temel adıyla başlayıp geçici uzantılardan biriyle bitip bitmediğini kontrol et
            if filename.startswith(base_name_without_ext) and any(filename.endswith(ext) for ext in temp_extensions):
                full_path = os.path.join(db_dir, filename)
                try:
                    os.remove(full_path)
                    deleted_files.append(filename)
                    print(f"Silindi: {filename}")
                except OSError as e:
                    print(f"Hata: '{filename}' silinirken sorun oluştu (muhtemelen kilitli): {e}")
    except FileNotFoundError:
        print(f"Uyarı: Dizin bulunamadı veya erişilemiyor: '{db_dir}'. Geçici dosyalar temizlenemedi.")
    except Exception as e:
        print(f"Beklenmedik bir hata oluştu: {e}")

    if deleted_files:
        print(f"Toplam {len(deleted_files)} adet geçici dosya silindi.")
    else:
        print("Herhangi bir geçici SQLite dosyası bulunamadı.")




class GirisPenceresi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_makul()
        self.ui.setupUi(self)
        self.ui.chs.stateChanged.connect(self.sifre_goster_gizle)
        self.ui.pbgir.clicked.connect(self.giris_yap)
        self.ui.lipos.setEchoMode(self.ui.lipos.Normal)
        self.db_path="sehir.db"
        
    def sifre_goster_gizle(self):
        if self.ui.chs.isChecked():
            self.ui.lisif.setEchoMode(self.ui.lisif.Normal)
        else:
            self.ui.lisif.setEchoMode(self.ui.lisif.Password)

    def giris_yap(self):
        kullanici_adi = self.ui.liad.text().strip()
        eposta = self.ui.lipos.text().strip()
        sifre = self.ui.lisif.text()

        if not kullanici_adi or not eposta or not sifre:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen tüm alanları doldurunuz.")
            return

        if len(sifre) < 8:
            QMessageBox.warning(self, "Şifre Hatası", "Şifre en az 8 karakter olmalıdır.")
            return

         
        with sqlite3.connect("sehir.db") as conn:  # Veritabanı 
            curs = conn.cursor()
            curs.execute("SELECT idkul FROM kullanicigirisi WHERE kuladi=? AND eposta=? AND password=?", 
                         (kullanici_adi, eposta, sifre))
            sonuc = curs.fetchone()

            if sonuc:
                self.kullanici_id = sonuc[0]  # Kullanıcı ID'sini sakla
                QMessageBox.information(self, "Başarılı Giriş", f"Hoş geldiniz, {kullanici_adi}!")
                self.ana_pencereyi_ac(self.kullanici_id)
            else:
                    QMessageBox.critical(self, "Hatalı Giriş", "Kullanıcı bilgileri hatalı!")

    def ana_pencereyi_ac(self,kullanici_id):
        self.ana_pencere = Anapencere(kullanici_id)
        self.ana_pencere.show()
        self.close()

class Anapencere(QMainWindow):
    def __init__(self,kullanici_id):
        super().__init__()
        self.ui = Ui_magezi()
        self.ui.setupUi(self)
        self.db_path = "sehir.db" 
        self.kullanici_id = kullanici_id
        
        clean_sqlite_temp_files(self.db_path)
        self.combo_box_doldur()
        self.ilktik=True
        self.baslangictarihi = None
        self.bitistarihi = None
        self.guncellenecekid=None
        self.ui.cseh.currentIndexChanged.connect(self.sehir_secildi)
        
        try:
           self.ui.pbkay.clicked.disconnect()
        except Exception:
           pass
      
        self.ui.pbkay.clicked.connect(self.kaydet_buton_clicked)
        self.ui.pbara.clicked.connect(self.ara)
        self.ui.pbsil.clicked.connect(self.sil)
        self.ui.pbek.clicked.connect(self.ekle_basildi)
        self.ui.pbd.clicked.connect(self.duzenle)
        self.ui.pbc.clicked.connect(self.kapat)
  
      

        self.ui.calendarWidget.selectionChanged.connect(self.tarih_secildi)
        self.tabloya_verileri_yukle(kullanici_id)
       
        
        self.ui.pbkay.setEnabled(False)
        self.ui.cseh.setEnabled(False)
        self.ui.ctur.setEnabled(False)
        self.ui.labbas.clear()
        self.ui.labbit.clear()
        
    def kaydet_buton_clicked(self):
        if hasattr(self, 'guncellenecekid') and self.guncellenecekid:
            self.kaydet2()  # Güncelle
        else:
            self.kaydet()   # Yeni ekle
    
    def combo_box_doldur(self):#burda sade gosterılıyo
         """
         Şehir ve Tur ComboBox'larını veritabanındaki mevcut verilerle doldurur.
         """
         self.ui.cseh.clear()
         self.ui.ctur.clear()
         try:
             with sqlite3.connect(self.db_path) as conn:
                 curs = conn.cursor()
                 curs.execute("SELECT sehirismi FROM sehir ORDER BY sehirismi")
                 sehirler = [row[0] for row in curs.fetchall()]
                 for sehir in sehirler:
                     self.ui.cseh.addItem(sehir)

                 curs.execute("SELECT turismi FROM tur ORDER BY turismi")
                 turlar = [row[0] for row in curs.fetchall()]
                 for tur in turlar:
                     self.ui.ctur.addItem(tur)
         except sqlite3.Error as e:
             QMessageBox.warning(self, "Veritabanı Hatası", f"ComboBox'lar doldurulurken hata oluştu: {e}")
   
    def tarih_secildi(self):
        secilentar = self.ui.calendarWidget.selectedDate()
        if self.ilktik:
            self.baslangictarihi = secilentar
            self.ui.labbas.setText(self.baslangictarihi.toString("dd.MM.yyyy"))
            self.ui.labbit.clear()
            self.bitistarihi = None
            self.ilktik = False
        else:
            if secilentar <= self.baslangictarihi:
                QMessageBox.warning(self, "Hatalı Tarih", "Bitiş tarihi, başlangıç tarihinden önce olamaz. Lütfen tekrar seçin.")
                self.ui.labbas.clear()
                self.ui.labbit.clear()
                self.baslangictarihi = None
                self.bitistarihi = None
                self.ilktik = True
                return
            self.bitistarihi = secilentar
            self.ui.labbit.setText(self.bitistarihi.toString("dd.MM.yyyy"))
            self.ilktik = True
    
    def sehir_secildi(self):
        secilen_sehir = self.ui.cseh.currentText()
        self.ui.ctur.clear()

        baglanti = sqlite3.connect("sehir.db")
        imlec = baglanti.cursor()
        
        imlec.execute("""
            SELECT tur.turismi
            FROM tur
            JOIN tursehir ON tur.idtur = tursehir.idtur
            JOIN sehir ON tursehir.idsehir = sehir.idsehir
            WHERE sehir.sehirismi = ?
        """, (secilen_sehir,))

        tur_listesi = imlec.fetchall()

        for tur in tur_listesi:
            self.ui.ctur.addItem(tur[0])

        baglanti.close()

    def ekle_basildi(self):
        if not self.baslangictarihi or not self.bitistarihi:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce takvimden başlangıç ve bitiş tarihlerini seçin!")
            return

        self.ui.cseh.setEnabled(True)
        self.ui.ctur.setEnabled(True)
        self.ui.pbkay.setEnabled(True)
        QMessageBox.information(self, "Bilgi", "Tarihler seçildi. Şimdi şehir ve tur seçip 'Kaydet' butonuna basabilirsiniz.")

        if self.ui.cseh.currentIndex() == -1:
            if self.ui.cseh.count() > 0:
                self.ui.cseh.setCurrentIndex(0)
            else:
                QMessageBox.warning(self, "Uyarı", "Veritabanında hiç şehir bulunamadı. Lütfen önce şehir ekleyin.")
                self.ui.cseh.setEnabled(False)
                self.ui.ctur.setEnabled(False)
                self.ui.pbkay.setEnabled(False)
                return

        
    
    def sehir_id_getir(self, sehirad):
        with sqlite3.connect(self.db_path) as conn:
           curs = conn.cursor()
           curs.execute("SELECT idsehir FROM sehir WHERE sehirismi = ?", (sehirad,))
           sonuc = curs.fetchone()
           return sonuc[0] if sonuc else None

    def tur_id_getir(self, turad):
        with sqlite3.connect(self.db_path) as conn:
           curs = conn.cursor()
           curs.execute("SELECT idtur FROM tur WHERE turismi = ?", (turad,))
           sonuc = curs.fetchone()
           return sonuc[0] if sonuc else None

    
    def tabloya_verileri_yukle(self, kullanici_id):
      try: 
       self.ui.tabseh.setRowCount(0)  # Tabloyu temizle
       with sqlite3.connect(self.db_path) as conn:
           curs = conn.cursor()
           sorgu = """
                SELECT 
                   t.idtarih, 
                   GROUP_CONCAT(s.sehirismi, ', ') AS sehirler, 
                   tr.turismi, 
                   t.bastarihad, 
                   t.bittarihad
               FROM tarih t
               JOIN tur tr ON t.turidtur = tr.idtur
               JOIN tursehir ts ON ts.idtur = tr.idtur
               JOIN sehir s ON ts.idsehir = s.idsehir
               WHERE t.idkulid = ?
               GROUP BY t.idtarih, tr.turismi, t.bastarihad, t.bittarihad
           """
           curs.execute(sorgu, (kullanici_id,))
           kayıtlar = curs.fetchall()
           self.ui.tabseh.setColumnCount(5)
           for (idtarih, sehir, tur, bastarih, bittarih) in kayıtlar:
               self.ui.tabseh.insertRow(0)  # Satırı en üste ekle

               try:
                    bastarih_dt = datetime.strptime(bastarih, "%Y-%m-%d")
                    bastarih_str = bastarih_dt.strftime("%d.%m.%Y")  # Gün.ay.yıl şeklinde
               except Exception:
                    bastarih_str = str(bastarih)  # Eğer format beklenmedik ise olduğu gibi al

               try:
                    bittarih_dt = datetime.strptime(bittarih, "%Y-%m-%d")
                    bittarih_str = bittarih_dt.strftime("%d.%m.%Y")
               except Exception:
                    bittarih_str = str(bittarih)
               self.ui.tabseh.setItem(0, 0, QTableWidgetItem(sehir))
               self.ui.tabseh.setItem(0 ,1, QTableWidgetItem(tur))
               self.ui.tabseh.setItem(0, 2, QTableWidgetItem(bastarih_str))
               self.ui.tabseh.setItem(0,3,QTableWidgetItem(bittarih_str))
               # idtarih bilgisini gizli data olarak sakla, örneğin 3. sütun
               id_item = QTableWidgetItem(str(idtarih))
               id_item.setData(Qt.UserRole, idtarih)
               self.ui.tabseh.setItem(0, 4, id_item)
           self.ui.tabseh.setColumnHidden(4, True)     
      except Exception as e:
          print(f"tablo yuklenırken hata olustu{e}")
     
    def tur_adi_var_mi(self, tur_adi):
        with sqlite3.connect(self.db_path) as conn:
            curs = conn.cursor()
            sorgu = "SELECT COUNT(*) FROM tur WHERE turismi = ?"
            curs.execute(sorgu, (tur_adi,))
            sonuc = curs.fetchone()
            return sonuc[0] > 0
   
    def kaydet(self):
        # Eğer düzenleme modunda ise, kaydet2'yi çağır (güncelle)
        if hasattr(self, 'guncellenecekid') and self.guncellenecekid:
            self.kaydet2()
            return
        if not self.baslangictarihi or not self.bitistarihi:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce başlangıç ve bitiş tarihlerini seçin!")
            return
        # 3 günlük sınır kontrolü
        fark = self.baslangictarihi.daysTo(self.bitistarihi)
        if fark > 2:
            QMessageBox.warning(self, "Uyarı", "Gezi süresi en fazla 3 gün olabilir!")
            return
        sehir = self.ui.cseh.currentText()
        tur = self.ui.ctur.currentText()

        if not sehir or not tur:
            QMessageBox.warning(self, "Uyarı", "Lütfen şehir ve tur seçiniz!")
            return
      
        baslangic_str = self.baslangictarihi.toString("yyyy-MM-dd")
        bitis_str = self.bitistarihi.toString("yyyy-MM-dd")
        
        sehir_id = self.sehir_id_getir(sehir)
        tur_id = self.tur_id_getir(tur)

        if sehir_id is None or tur_id is None:
            QMessageBox.critical(self, "Hata", "Şehir veya tur bilgisi veritabanında bulunamadı!")
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                curs = conn.cursor()
                # tarih tablosuna ekleme yapıyoruz, burada idkul kullanici_id'dir
                sorgu = """
                    INSERT INTO tarih (idkulid, turidtur, bastarihad, bittarihad) 
                    VALUES (?, ?, ?, ?)
                """
                curs.execute(sorgu, (self.kullanici_id, tur_id, baslangic_str, bitis_str))
                conn.commit()
                
            QMessageBox.information(self, "Başarılı", "Gezi planınız kaydedildi!")
            self.tabloya_verileri_yukle(self.kullanici_id)  # Tabloyu güncelle
            self.baslangictarihi = None
            self.bitistarihi = None
            self.ui.labbas.clear()
            self.ui.labbit.clear()
            self.ui.cseh.setCurrentIndex(0)
            self.ui.ctur.setCurrentIndex(0)
            self.ui.pbkay.setEnabled(False)
            self.ui.cseh.setEnabled(False)
            self.ui.ctur.setEnabled(False)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Veritabanı Hatası", f"Veri kaydedilirken hata oluştu: {e}")
      
    
    def tabloya_yeni_gezi_ekle(self, idtarih, sehir, tur, bastarih, bittarih):
        self.ui.tabseh.insertRow(0)
        bastarih_str = bastarih.strftime("%d.%m.%Y") if hasattr(bastarih, "strftime") else str(bastarih)
        bittarih_str = bittarih.strftime("%d.%m.%Y") if hasattr(bittarih, "strftime") else str(bittarih)
        
        self.ui.tabseh.setItem(0, 0, QTableWidgetItem(sehir))
        self.ui.tabseh.setItem(0, 1, QTableWidgetItem(tur))
        self.ui.tabseh.setItem(0, 2, QTableWidgetItem(f"{bastarih_str} - {bittarih_str}"))

        id_item = QTableWidgetItem(str(idtarih))
        id_item.setData(Qt.UserRole, idtarih)
        self.ui.tabseh.setItem(0, 3, id_item)

        self.ui.tabseh.setColumnHidden(3, True)  # ID kolonunu gizliyoruz
        
    def ara(self):
        arama_kelimesi = self.ui.liara.text().strip().lower()

        for satir in range(self.ui.tabseh.rowCount()):
            sehir_item = self.ui.tabseh.item(satir, 0)  # Şehir ismi sütunu
            tur_item = self.ui.tabseh.item(satir, 1)    # Tur ismi sütunu

            sehir = sehir_item.text().lower() if sehir_item else ""
            tur = tur_item.text().lower() if tur_item else ""

            if arama_kelimesi in sehir or arama_kelimesi in tur:
                self.ui.tabseh.setRowHidden(satir, False)  # Göster
            else:
                self.ui.tabseh.setRowHidden(satir, True)   # Gizle


    def duzenle(self):
        
   
        selected_row = self.ui.tabseh.currentRow()
        if selected_row < 0:
                QMessageBox.warning(self, "Uyarı", "Lütfen düzenlemek için bir satır seçin.")
                return
        idtarih_item = self.ui.tabseh.item(selected_row, 4)
        if idtarih_item is None:
            QMessageBox.warning(self, "Hata", "Seçilen satırda ID bulunamadı.")
            return
        
        self.guncellenecekid = idtarih_item.data(Qt.UserRole)
        if self.guncellenecekid is None:
           QMessageBox.warning(self, "Hata", "Seçilen satırda geçerli ID bulunamadı.")
           return

        baslangic_str = self.ui.tabseh.item(selected_row, 2).text()  # Başlangıç tarihi
        bitis_str = self.ui.tabseh.item(selected_row, 3).text()     # Bitiş tarihi
        

        baslangic_date = QDate.fromString(baslangic_str, "dd.MM.yyyy")
        bitis_date = QDate.fromString(bitis_str, "dd.MM.yyyy")
        
        if not baslangic_date.isValid() or not bitis_date.isValid():
            QMessageBox.warning(self, "Hata", "Tarih formatı geçersiz.")
            return
        self.baslangictarihi = baslangic_date
        self.bitistarihi = bitis_date
        # Label'lara tarihi yazdır
        self.ui.labbas.setText(baslangic_date.toString("dd.MM.yyyy"))
        self.ui.labbit.setText(bitis_date.toString("dd.MM.yyyy"))
        # Comboboxları pasif yap: değiştirilmesin, sadece gösterilsin
        self.ui.cseh.setEnabled(False)
        self.ui.ctur.setEnabled(False)

        try:
            self.ui.pbkay.clicked.disconnect()
        except TypeError:
           pass
        self.ui.pbkay.clicked.connect(self.kaydet2)

        self.ui.pbkay.setEnabled(True)
        self.ui.cseh.setEnabled(False)
        self.ui.ctur.setEnabled(False)
     
     
        
    
    
    def kaydet2(self):    
        
    # Düzenleme modundaysak guncellenecekid var mı kontrol et
        if not hasattr(self, 'guncellenecekid') or not self.guncellenecekid:
            QMessageBox.warning(self, "Uyarı", "Güncellenecek kayıt seçili değil!")
            return
        
    
        if not self.baslangictarihi or not self.bitistarihi:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce başlangıç ve bitiş tarihlerini seçin!")
            return
        # 3 günlük sınır kontrolü
        fark = self.baslangictarihi.daysTo(self.bitistarihi)
        if fark > 2:
            QMessageBox.warning(self, "Uyarı", "Gezi süresi en fazla 3 gün olabilir!")
            return
      
    
        baslangic_str = self.baslangictarihi.toString("yyyy-MM-dd")
        bitis_str = self.bitistarihi.toString("yyyy-MM-dd")
    
  
      
        try:
            with sqlite3.connect(self.db_path) as conn:
                curs = conn.cursor()
                # Güncelleme sorgusu
                sorgu = """
                   UPDATE tarih
                   SET bastarihad = ?, bittarihad = ?
                   WHERE idtarih = ? AND idkulid = ?
                """
                curs.execute(sorgu, ( baslangic_str, bitis_str, self.guncellenecekid, self.kullanici_id))
                conn.commit()
        
            QMessageBox.information(self, "Başarılı", "Gezi planınız güncellendi!")
            self.tabloya_verileri_yukle2(self.kullanici_id)  # Tabloyu güncelle
            # Formu temizle ve düzenleme modundan çık
            self.temizle_form()
            self.guncellenecekid = None
            # Kaydet butonunun sinyalini tekrar kaydet fonksiyonuna bağla
            try:
                self.ui.pbkay.clicked.disconnect()
            except TypeError:
                    pass
            self.ui.pbkay.clicked.connect(self.kaydet)    
            # Temizle
            
            self.baslangictarihi = None
            self.bitistarihi = None
            self.ui.labbas.clear()
            self.ui.labbit.clear()
            self.ui.pbkay.setEnabled(False)
            self.ui.cseh.setEnabled(False)
            self.ui.ctur.setEnabled(False)
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Veritabanı Hatası", f"Veri güncellenirken hata oluştu: {e}") 
            
    def tabloya_verileri_yukle2(self, kullanici_id):
        try:
            self.ui.tabseh.setRowCount(0)  # Tabloyu temizle
            with sqlite3.connect(self.db_path) as conn:
                curs = conn.cursor()
                sorgu = """
                  SELECT 
                  t.idtarih, 
                  GROUP_CONCAT(s.sehirismi, ', ') AS sehirler, 
                  tr.turismi, 
                  t.bastarihad, 
                  t.bittarihad
              FROM tarih t
              JOIN tur tr ON t.turidtur = tr.idtur
              JOIN tursehir ts ON ts.idtur = tr.idtur
              JOIN sehir s ON ts.idsehir = s.idsehir
              WHERE t.idkulid = ?
              GROUP BY t.idtarih, tr.turismi, t.bastarihad, t.bittarihad

                """
                curs.execute(sorgu, (kullanici_id,)) 
                kayıtlar=curs.fetchall()
                self.ui.tabseh.setColumnCount(5)
                for idx, (idtarih, sehir, tur, bastarih, bittarih) in enumerate(kayıtlar):
                    self.ui.tabseh.insertRow(idx)
                    
                    try:
                        bastarih_dt = datetime.strptime(bastarih, "%Y-%m-%d")
                        bastarih_str = bastarih_dt.strftime("%d.%m.%Y")
                    except Exception:
                        bastarih_str = str(bastarih)
                   
                    try:
                        bittarih_dt = datetime.strptime(bittarih, "%Y-%m-%d")
                        bittarih_str = bittarih_dt.strftime("%d.%m.%Y")
                    except Exception:
                        bittarih_str = str(bittarih)
                    self.ui.tabseh.setItem(idx, 0, QTableWidgetItem(sehir))
                    self.ui.tabseh.setItem(idx, 1, QTableWidgetItem(tur))
                    self.ui.tabseh.setItem(idx, 2, QTableWidgetItem(bastarih_str))
                    self.ui.tabseh.setItem(idx, 3, QTableWidgetItem(bittarih_str))

                    id_item = QTableWidgetItem(str(idtarih))
                    id_item.setData(Qt.UserRole, idtarih)
                    self.ui.tabseh.setItem(idx, 4, id_item)

                self.ui.tabseh.setColumnHidden(4, True)
                
                

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Veritabanı Hatası", f"Güncelleme sonrası tablo yenileme hatası: {e}")
    def temizle_form(self):
        self.ui.labbas.clear()
        self.ui.labbit.clear()
        self.baslangictarihi = None
        self.bitistarihi = None
        self.ui.cseh.setCurrentIndex(0)
        self.ui.ctur.setCurrentIndex(0)
    
    def sil(self):
        selected_row = self.ui.tabseh.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek için bir satır seçin.")
            return

        id_item = self.ui.tabseh.item(selected_row, 4)
        if id_item is None:
            QMessageBox.warning(self, "Hata", "Seçilen satırdan ID bilgisi alınamadı.")
            return
        idtarih = id_item.data(Qt.UserRole)
        if idtarih is None:
            QMessageBox.warning(self, "Hata", "Seçilen satırın ID bilgisi alınamadı.")
            return

        cevap = QMessageBox.question(self, "Onay", "Seçili kaydı silmek istediğinize emin misiniz?",
                                 QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    curs = conn.cursor()
                    curs.execute("DELETE FROM tarih WHERE idtarih = ?", (idtarih,))
                    conn.commit()
               
                self.tabloya_verileri_yukle(self.kullanici_id)  # Verileri güncelle
                # Temizle
                self.guncellenecekid = None
                self.baslangictarihi = None
                self.bitistarihi = None
                self.ui.labbas.clear()
                self.ui.labbit.clear()
                self.ui.cseh.setCurrentIndex(0)
                self.ui.ctur.setCurrentIndex(0)
                self.ui.pbkay.setEnabled(False)
                self.ui.cseh.setEnabled(False)
                self.ui.ctur.setEnabled(False)
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Hata", f"İşlem başarısız: {str(e)}")

    def kapat(self):
       cevap = QMessageBox.question(
           self,
           "Uygulamayı Kapat",
           "Uygulamadan çıkmak istediğinize emin misiniz?",
           QMessageBox.Yes | QMessageBox.No,
           QMessageBox.No
       )
       if cevap == QMessageBox.Yes:
            self.close()

    def closeEvent(self, event):
        """Uygulama kapatıldığında veritabanı bağlantısını kapatır ve geçici dosyaları temizler."""
        print("Uygulama kapatılıyor...")
        clean_sqlite_temp_files(self.db_path)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = GirisPenceresi()
    pencere.setWindowTitle("Giriş Ekranı")
    pencere.setWindowIcon(QIcon("icon.png"))
    pencere.show()
    sys.exit(app.exec_())