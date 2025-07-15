import streamlit as st
import pandas as pd

st.title(' Machine Learning  App')

st.info('ML Model App')

with st.expander('Data'):
    st.write('**Raw data**')
    df = pd.read_csv('PinConversation.csv')
    df

    st.write('**X**')
    X = df.drop('content', axis=1)
    X

    st.write('**Y**')
    y = df.content
    y

with st.expander('Data visualization'):
    # uuid, size
    st.scatter_chart(data=df, x='uuid', y='size', color='content')

# Data preperations
with st.sidebar:
    st.header('Input features')
    # request.header.accept-encoding
    Time = st.selectbox('request.header.accept-encoding', ('gzip', 'deflate', 'br'))

