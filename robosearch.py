'''

conda create -n robotica python==3.9
conda activate robotica
sudo apt install python3-dev
sudo apt-get install build-essential -y
pip install pypdf
pip install openai
pip install tiktoken
conda install pandas
pip install txtai
pip install streamlit


conda activate robotica
cd /home/cirillo/Desktop/Robotica2
streamlit run robosearch.py


https://www.learndatasci.com/tutorials/python-pandas-tutorial-complete-introduction-for-beginners/
https://pandas.pydata.org/docs/user_guide/10min.html




'''

import pandas as pd
import streamlit as st
import json
import base64
from txtai.embeddings import Embeddings
import time
# # load documents
import os
import uuid
import re 
import tempfile

embeddings = Embeddings(path="sentence-transformers/nli-mpnet-base-v2", content=True, objects=True)
embeddings.load("Exams_dictio2")


file_path='Exams_dictio.json'
options = {'file': [], 'date': [],'num_ex': [],'exam': [],'question': [],'solution': [],'robot': [],'tags': []}




def displayPDF(file):
    # Opening file from file path
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        print('LOADED')


    # Embedding PDF in HTML
    try:
        pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000" type="application/pdf"></iframe>'
    except:
        pdf_display = F'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'


    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)


def search_complex(query, db, collection, k, tag = None):
    embeddings = OpenAIEmbeddings()
    collection = Chroma(collection, embeddings, persist_directory = db)

    # $eq: equal to (previously used).
    # $ne: not equal to.
    # $gt: greater than.
    # $gte: greater than or equal to.
    # $lt: less than.
    # $lte: less than or equal to.
    # where_clause = {
    #     "$and" : [
    #         {"GICS Sector" : {"$eq": "Information Technology"}}, 
    #         {"date_founded": {"$gte": 1990}}
    #     ]
    # }

    if tag == None:
        response = collection.similarity_search_with_score(
            query=query, 
            k = k, 
        )
    else:
        response = collection.similarity_search_with_score(
            query=query, 
            k = k, 
            # where = where_clause
            where_document= {"$contains": tag}
        )
    return response


def make_clickable(link):
    # target _blank to open new window
    # extract clickable text to display for your link
    link = str('Exam_archive/' + link)
    print('LINK: ', link)
    #return f'<a target="_blank" href="{link}">{link}</a>'
    return link

def get_robot_options(filename, options, key_t):
    f = open(file_path)
    data = json.load(f)
    for key in data.keys():
        for label in key_t:
            if data[key][label] not in options[label]:
                options[label].append(data[key][label])
        for tag in data[key]['tags']:
            if tag not in options['tags']:
                options['tags'].append(tag)

    return options

def dataframe_with_selections(df):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "View", False)
    df_with_selections['file'] = df_with_selections['file'].apply(make_clickable)
    #df_with_selections = df_with_selections.to_html(escape=False)

    edited_df = st.data_editor(
        df_with_selections, width=1900, 
            column_config={
            "View": st.column_config.CheckboxColumn(required=True),
            "file": st.column_config.LinkColumn("file"),
            "date": "date",
            "num_ex": "ex",
            "question": "question",
            "solution": "solution",
            "robot": "robot",
            "tags": "tags",
        },
        hide_index=True,
        column_order=("View", "file", "date", "num_ex", "question", "solution", "robot", "tags")
        )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.View]
    return selected_rows.drop('View', axis=1)

def question(text, limite):
  return embeddings.search(f"select key, score from txtai where similar('{text}') limit {limite}")

def load_data(filename, options, key_t, row1_text, row2_text, type_emb='normal'):
    with open(file_path) as my_file:
        data = json.load(my_file)

        if row1_text != '':
            if type_emb == 'txtai':
                if row1_text != '':
                    data_search = question(row1_text, 20)
                    print('****   SEARCH DONE! ****')
                    print(data_search)
                    exam_list = []
                    for key in data_search:
                        chiave = key['key']
                        append = True
                        for label in key_t:
                            if data[chiave][label] not in options[label]:
                                append = False
                        if append:
                            exam_list.append(data[chiave])
        else:
            exam_list = []
            for key in data.keys():
                append = True
                for label in key_t:
                    if data[key][label] not in options[label]:
                        append = False
                if append:
                    exam_list.append(data[key])

        data = None
        return exam_list


st.set_page_config(layout="wide")
st.title('Robotics2 - Exercises')
tab1, tab2, tab3 = st.tabs(["Exercises", "Theory", "Appendix"])

with tab1:
    st.header("    SEARCH       ")
    key_t = ['robot', 'exam']
    options_list = get_robot_options(file_path, options, key_t)

    with st.form("my_form"):
        header = st.columns([2,2])
        header[0].subheader('Semantic Search')
        header[1].subheader('Word Search')
        # header[2].subheader('Tags Search')
        # header[3].subheader('Params Search')

        row1 = st.columns([2,2])
        txt = row1[0].text_area('Inserisci il testo per la ricerca semantica', '''''')
        tags = row1[1].text_input('Cerca una parola nel testo', '')
        option_embedding = 'txtai'
        if option_embedding == 'Get Everything files':
            txt = ''
            tags = ''
        # options_list['tags'] = row1[2].multiselect('Tags (lasciare vuoto per prendere TUTTO)', options_list['tags'], [])
        # options_list['robot'] = row1[3].multiselect('Robot', options_list['robot'], options_list['robot'])
        st.form_submit_button('SEARCH', use_container_width= True, type = "primary")

    print(options_list)
    print('row1.textarea ', txt)
    df = pd.DataFrame(load_data(file_path, options_list, key_t, txt, tags, option_embedding))
    selection = dataframe_with_selections(df)

    # st.write(len(selection['file']))
    # st.write(selection['file'])
    
    # elements = []
    # num_choose = len(selection['file'])
    # if num_choose > 0:
    #     buttons = st.columns([1]*num_choose)
    #     for i, element in enumerate(selection['file']):
    #         if element not in elements:
    #             elements.append(element)

    #     for i, element in enumerate(elements):
    #         if buttons[i].button(element, key=i+1):
    #             st.write(element)
    #             file_pdf = '/home/cirillo/Desktop/Robotica2/Exam_archive/' + element
    #             displayPDF(file_pdf)

# with tab2:
#    st.header("      TAB2        ")
#    st.write('TAB2')

# with tab3:
#    st.header("      TAB3        ")
#    st.write('TAB3')



