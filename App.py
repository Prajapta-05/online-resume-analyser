import streamlit as st
import pandas as pd
import base64,random # base64-it just converts binary data into text using 64 ASCII characters (A–Z, a–z, 0–9, +, /).
import time,datetime
from pyresparser import ResumeParser # library extract name,email,mobile numbers skills, degree, college name, company names
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io,random
from streamlit_tags import st_tags #shows tags
from PIL import Image
import pymysql #will help to connect to sql database
from Courses import ds_course,web_course,android_course,ios_course,uiux_course,resume_videos,interview_videos
import spacy
nlp = spacy.load("en_core_web_sm")
import plotly.express as px #to create visualisations at the admin session
import nltk
nltk.download('stopwords')
from yt_dlp import YoutubeDL

def fetch_yt_video(link):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "nocheckcertificate": True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)

            if info is None:
                return None

            # Handle playlists or redirects
            if "entries" in info:
                info = info["entries"][0]

            return info.get("title")

    except Exception as e:
        print("YT ERROR:", e)
        return None
def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 🎓**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


# CONNECT TO DATABASE
import os

connection = pymysql.connect(
    host=os.environ.get('DB_HOST', 'localhost'),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', 'password'),
    db=os.environ.get('DB_NAME', 'cv')
)
cursor = connection.cursor()


def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills,
                courses):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (
    name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills,
    courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()


st.set_page_config(
    page_title="Resume Analyzer",
    page_icon='./Logo/logo3.png',
)


def run():
    img = Image.open('./Logo/logo3.png')
    img = img.resize((600,150))
    st.image(img)
    st.title("Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)



    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(500) NOT NULL,
                     Email_ID VARCHAR(500) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field BLOB NOT NULL,
                     User_level BLOB NOT NULL,
                     Actual_skills BLOB NOT NULL,
                     Recommended_skills BLOB NOT NULL,
                     Recommended_courses BLOB NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)
    if choice == 'User':
        st.markdown(
            '''<h5 style='text-align: left; color: #021659;'> Upload your resume, and get smart recommendations</h5>''',
            unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Uploading your Resume...'):
                time.sleep(4)
            save_pdf_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_pdf_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_pdf_path)
            resume_data = ResumeParser(save_pdf_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_pdf_path)
                import re

                # --- Clean Email (IMPORTANT FIX) ---
                email_match = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", resume_text)

                email = None
                for e in email_match:
                    if "@" in e and "." in e:
                        email = e
                        break

                if not email:
                    email = resume_data.get('email', 'Not Found')

                st.header("**Resume Analysis**")

                # -------- FINAL NAME EXTRACTION (STRONG + RELIABLE) --------

                name = None
                lines = resume_text.split('\n')

                # STEP 1: Get first clean line (MOST RELIABLE)
                for line in lines[:10]:
                    line = line.strip()

                    if not line:
                        continue

                    # skip garbage lines
                    if any(x in line.lower() for x in [
                        'resume', 'curriculum', 'vitae',
                        'email', 'phone', 'contact',
                        'linkedin', 'github'
                    ]):
                        continue

                    # skip lines with digits or symbols
                    if any(char.isdigit() for char in line):
                        continue

                    # valid name pattern (2–4 words, only alphabets)
                    words = line.split()
                    if 2 <= len(words) <= 4 and all(word.isalpha() for word in words):
                        name = line
                        break

                # STEP 2: fallback → spaCy
                if not name:
                    doc = nlp(resume_text)
                    for ent in doc.ents:
                        if ent.label_ == "PERSON":
                            name = ent.text
                            break

                # STEP 3: last fallback
                if not name:
                    name = "Candidate"


                st.success("Hello " + name)
                st.subheader("**Your Basic info**")

                try:
                    st.text('Name: ' + name)
                    st.text('Email: ' + email)
                    st.text('Contact: ' + str(resume_data.get('mobile_number', 'Not Found')))
                    st.text('Resume pages: ' + str(resume_data.get('no_of_pages', '0')))
                except:
                    pass
                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>''',
                                unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                                unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >= 3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                                unsafe_allow_html=True)

                # st.subheader("**Skills Recommendation💡**")
                ## Skill shows
                keywords = st_tags(label='### Your Current Skills',
                                   text='See our skills recommendation below',
                                   value=resume_data['skills'], key='1  ')

                ##  keywords
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep Learning', 'flask',
                              'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes',
                                'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro',
                                'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp',
                                'user research', 'user experience']

                recommended_skills = []
                reco_field = ''
                rec_course = ''

                # STEP 1: Only detect field and set variables inside the loop, NO widgets here
                for i in resume_data['skills']:
                    if i.lower() in ds_keyword:
                        reco_field = 'Data Science'
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling',
                                              'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                              'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras',
                                              'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask",
                                              'Streamlit']
                        break

                    elif i.lower() in web_keyword:
                        reco_field = 'Web Development'
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel', 'Magento',
                                              'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        break

                    elif i.lower() in android_keyword:
                        reco_field = 'Android Development'
                        recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java',
                                              'Kivy', 'GIT', 'SDK', 'SQLite']
                        break

                    elif i.lower() in ios_keyword:
                        reco_field = 'IOS Development'
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation',
                                              'Auto-Layout']
                        break

                    elif i.lower() in uiux_keyword:
                        reco_field = 'UI-UX Development'
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq',
                                              'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing',
                                              'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe',
                                              'Solid', 'Grasp', 'User Research']
                        break

                else:
                    reco_field = 'General'
                    recommended_skills = ['Communication', 'Problem Solving', 'Critical Thinking',
                                          'Project Management', 'Microsoft Office', 'Data Analysis',
                                          'Time Management', 'Teamwork', 'Leadership', 'Adaptability']

                # STEP 2: Now display everything ONCE outside the loop, with a single fixed key
                if reco_field == 'Data Science':
                    st.success("** Our analysis says you are looking for Data Science Jobs.**")
                    rec_course = course_recommender(ds_course)

                elif reco_field == 'Web Development':
                    st.success("** Our analysis says you are looking for Web Development Jobs **")
                    rec_course = course_recommender(web_course)

                elif reco_field == 'Android Development':
                    st.success("** Our analysis says you are looking for Android App Development Jobs **")
                    rec_course = course_recommender(android_course)

                elif reco_field == 'IOS Development':
                    st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                    rec_course = course_recommender(ios_course)

                elif reco_field == 'UI-UX Development':
                    st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                    rec_course = course_recommender(uiux_course)

                else:
                    st.warning(
                        "⚠️ We could not detect a specific field from your skills. Showing general recommendations.")
                    rec_course = course_recommender(ds_course)

                # ✅ Single st_tags call with one fixed key — no duplication possible
                recommended_keywords = st_tags(label='### Recommended skills for you.',
                                               text='Recommended skills generated from System',
                                               value=recommended_skills,
                                               key='recommended_skills_widget')

                st.markdown(
                    '''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to your resume will boost🚀 the chances of getting a Job💼</h4>''',
                    unsafe_allow_html=True)
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)

                ### Resume writing recommendation
                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if 'Objective' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add your career objective, it will give your career intension to the Recruiters.</h4>''',
                        unsafe_allow_html=True)

                if 'Declaration' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Delcaration/h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Declaration. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',
                        unsafe_allow_html=True)

                if 'Hobbies' in resume_text or 'Interests' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Hobbies. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',
                        unsafe_allow_html=True)

                if 'Achievements' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Achievements. It will show that you are capable for the required position.</h4>''',
                        unsafe_allow_html=True)

                if 'Projects' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Projects. It will show that you have done work related the required position or not.</h4>''',
                        unsafe_allow_html=True)

                st.subheader("**Resume Score📝**")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success('** Your Resume Writing Score: ' + str(score) + '**')
                st.warning("** Note: This score is calculated based on the content that you have in your Resume. **")
                st.balloons()

                insert_data(name, email, str(resume_score), timestamp,
                            str(resume_data.get('no_of_pages', '0')), reco_field, cand_level,
                            str(resume_data.get('skills', [])),
                            str(recommended_skills), str(rec_course))

                ## Resume writing video
                st.header("**Bonus Video for Resume Writing Tips💡**")
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)

                ## Interview Preparation Video
                st.header("**Bonus Video for Interview Tips💡**")
                interview_vid = random.choice(interview_videos)
                st.video(interview_vid)

            else:
                st.error('Something went wrong..')
    else:
        ## Admin Side
        st.success('Welcome to Admin Side')
        # st.sidebar.subheader('**ID / Password Required!**')

        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'Prajapta' and ad_password == 'password':
                st.success("Welcome Prajapta !")
                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                blob_cols = ['Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                             'Recommended Course']
                for col in blob_cols:
                    df[col] = df[col].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
                ## Admin Side Data
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)
                plot_data['Predicted_Field'] = plot_data['Predicted_Field'].apply(lambda x: x.decode() if isinstance(x, bytes) else x)
                plot_data['User_level'] = plot_data['User_level'].apply(lambda x: x.decode() if isinstance(x, bytes) else x)

                ## Pie chart for predicted field recommendations
                st.subheader("**Pie-Chart for Predicted Field Recommendation**")

                field_counts = plot_data['Predicted_Field'].value_counts().reset_index()
                field_counts.columns = ['Field', 'Count']

                fig = px.pie(field_counts, values='Count', names='Field',
                             title='Predicted Field according to Skills')

                st.plotly_chart(fig)

                ### Pie chart for User's👨‍💻 Experienced Level
                st.subheader("**Pie-Chart for User's Experienced Level**")

                level_counts = plot_data['User_level'].value_counts().reset_index()
                level_counts.columns = ['Level', 'Count']

                fig = px.pie(level_counts, values='Count', names='Level',
                             title="User Experience Level")

                st.plotly_chart(fig)


            else:
                st.error("Wrong ID & Password Provided")

import os
os.makedirs('./Uploaded_Resumes', exist_ok=True)
run()