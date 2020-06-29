import numpy as np
import cv2
from PIL import Image
import os
import mysql.connector

recognizer = cv2.face.LBPHFaceRecognizer_create()
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")


class SQL:
    def connect(self, ip ,u_id, u_pass,db):
        self.host = ip
        self.user = u_id
        self.password = u_pass
        self.database = db

        self.DB = mysql.connector.connect(host = self.host,user=self.user,passwd=self.password,database=self.database)

    def update(self, eid, status):
        self.mydb = self.DB.cursor()
        self.sql = "INSERT INTO `Attendance`.`Attendance_"+status+"` VALUES ("+eid+",NOW())"
        self.mydb.execute(self.sql)
        self.DB.commit()

    def new_id(self, eid, ename, edesg):
        self.mydb = self.DB.cursor()
        self.sql = "INSERT INTO `Attendance`.`Users` VALUES (" + eid + ",\""+ ename+ "\","+ "\""+ edesg +"\",NOW())"
        self.mydb.execute(self.sql)
        self.DB.commit()

class Train(SQL):
    name = ""
    user_list = []

    def __init__(self, im_source, usr, ref,cam,st):
        self.max = 0.0
        self.image_source = im_source
        self.user_path = usr
        self.reference = ref
        self.cam_index = cam
        self.status = st
        self.flag = True
    def check_user(self, dirname):
        if (dirname in os.listdir(self.image_source)):
            op = input("ID already Exists.\nDo you want to overwrite (y/n): ")
            if (op == 'n'):
                self.emp_id = input("Enter Your ID : ")
                self.check_user(self.emp_id)
            if (op == 'y'):
                self.flag = False

    def update_list(self, new):
        user_file = open(self.user_path, 'a+')
        user_file.write(new + "\n")
        user_file.close()

    def get_list(self):
        user_file = open(self.user_path, 'r')
        self.user_list = (user_file.read()).split("\n")
        user_file.close()

    def train(self):
        print("\nYour Image is being Processed")
        print("Please wait...........")
        self.get_list()
        sampling = []
        id = []
        for dir in os.listdir(self.image_source):
            for i in range(10):
                face = np.array(Image.open(self.image_source+dir+"/"+str(i+1)+".jpg").convert('L'),  'uint8')
                index = self.user_list.index(dir)
                output = face_cascade.detectMultiScale(face)

                for x, y, w, h in output:
                    sampling.append(face[y:y+h, x:x+w])
                    id.append(index)

        recognizer.train(sampling, np.array(id))
        recognizer.save(self.reference)
        print("\nTraining Complete.")
        print("Total Person Trained is {}".format(len(os.listdir(self.image_source))))

    def enroll(self):
        self.name = input("Enter the Name : ")
        self.desg = input("Enter Designation Name : ")
        self.emp_id = input("Enter the ID : ")
        self.check_user(self.emp_id)
        os.system("mkdir Images/"+self.emp_id)
        if self.flag:
            self.update_list(self.emp_id)
            SQL.new_id(self,self.emp_id,self.name,self.desg)
        no = 1

        camera = cv2.VideoCapture(self.cam_index)
        check, frame = camera.read()
        cv2.imwrite("Images/" + self.emp_id + "/Sample.jpg", frame)
        while 1:
            check, frame = camera.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            output = face_cascade.detectMultiScale(gray, 1.3, 5)

            for x, y, w, h in output:
                cv2.imwrite("Images/" + self.emp_id + "/" + str(no) + ".jpg", gray[y:y+h, x:x+w])
                no += 1
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 1)

            cv2.imshow("Video Feed", frame)

            k = cv2.waitKey(100) & 0xff
            if (k == 27) or (no > 10):
                camera.release()
                cv2.destroyAllWindows()
                self.train()
                break


class Recognise(Train):
    def run(self):
        self.get_list()
        camera = cv2.VideoCapture(self.cam_index)
        recognizer.read(self.reference)
        prev = 0
        while (1):
            check, frame = camera.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            output = face_cascade.detectMultiScale(gray, 1.3, 5)

            for x, y, w, h in output:
                id, confidence = recognizer.predict(gray[y:y + h, x:x + w])
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1)

                if (confidence > 100):
                    id = 0
                if (100 - confidence) > self.max:
                    self.max = 100 - confidence

                if (id != 0) and (prev != id):
                    SQL.update(self, self.user_list[id], self.status)
                    prev = id


                cv2.putText(frame, str(self.user_list[id]), (x + 5, y - 5),cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255),2)
                cv2.putText(frame, str("{:.2f}".format(100 - confidence)) + '%', (x + 5, y + h - 5),
                            cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 0), 1)

            cv2.imshow("Video Feed", frame)

            k = cv2.waitKey(100) & 0xff
            if (k == 27):
                camera.release()
                cv2.destroyAllWindows()
                break
