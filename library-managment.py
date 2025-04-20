import streamlit as st
import pandas as pd
import datetime
from PIL import Image
import os
import sqlite3

# Initialize database
def init_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS books
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  author TEXT,
                  isbn TEXT,
                  genre TEXT,
                  pages INTEGER,
                  year INTEGER,
                  publisher TEXT,
                  acquired_date DATE,
                  read_status TEXT,
                  rating INTEGER,
                  notes TEXT)''')
    conn.commit()
    conn.close()

# Initialize database connection
init_db()

# Book cover upload directory
os.makedirs("covers", exist_ok=True)

def add_book(book_data, cover_image=None):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Insert book data
    c.execute('''INSERT INTO books 
                 (title, author, isbn, genre, pages, year, publisher, 
                  acquired_date, read_status, rating, notes)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (book_data['title'], book_data['author'], book_data['isbn'], 
               book_data['genre'], book_data['pages'], book_data['year'], 
               book_data['publisher'], book_data['acquired_date'], 
               book_data['read_status'], book_data['rating'], 
               book_data['notes']))
    
    book_id = c.lastrowid
    
    # Save cover image if provided
    if cover_image:
        cover_path = f"covers/{book_id}.jpg"
        image = Image.open(cover_image)
        image.save(cover_path)
    
    conn.commit()
    conn.close()
    return book_id

def get_all_books():
    conn = sqlite3.connect('library.db')
    df = pd.read_sql('SELECT * FROM books', conn)
    conn.close()
    return df

def search_books(search_term, search_by='title'):
    conn = sqlite3.connect('library.db')
    query = f"SELECT * FROM books WHERE {search_by} LIKE ?"
    df = pd.read_sql(query, conn, params=(f'%{search_term}%',))
    conn.close()
    return df

def update_book(book_id, updates):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values())
    values.append(book_id)
    
    c.execute(f"UPDATE books SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_book(book_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id = ?", (book_id,))
    
    # Remove cover image if exists
    cover_path = f"covers/{book_id}.jpg"
    if os.path.exists(cover_path):
        os.remove(cover_path)
    
    conn.commit()
    conn.close()

def main():
    st.set_page_config(page_title="Personal Library Manager", page_icon="📚", layout="wide")
    
    st.title("📚 Personal Library Manager")
    st.write("Organize and manage your book collection")
    
    menu = ["Add Book", "View Library", "Search", "Statistics", "About"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Add Book":
        st.subheader("Add New Book")
        
        with st.form("add_book_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Title*", help="Required field")
                author = st.text_input("Author")
                isbn = st.text_input("ISBN")
                genre = st.selectbox("Genre", ["", "Fiction", "Non-Fiction", "Science Fiction", 
                                              "Fantasy", "Mystery", "Thriller", "Biography", 
                                              "History", "Self-Help", "Other"])
                pages = st.number_input("Pages", min_value=0, step=1)
                
            with col2:
                year = st.number_input("Publication Year", min_value=0, max_value=datetime.datetime.now().year)
                publisher = st.text_input("Publisher")
                acquired_date = st.date_input("Acquired Date", datetime.date.today())
                read_status = st.selectbox("Reading Status", ["Unread", "Reading", "Finished"])
                rating = st.slider("Rating (1-5)", 1, 5)
                
            notes = st.text_area("Notes")
            cover_image = st.file_uploader("Upload Cover Image", type=["jpg", "jpeg", "png"])
            
            submitted = st.form_submit_button("Add Book")
            
            if submitted:
                if not title:
                    st.error("Title is required!")
                else:
                    book_data = {
                        'title': title,
                        'author': author,
                        'isbn': isbn,
                        'genre': genre,
                        'pages': pages,
                        'year': year,
                        'publisher': publisher,
                        'acquired_date': acquired_date,
                        'read_status': read_status,
                        'rating': rating,
                        'notes': notes
                    }
                    
                    book_id = add_book(book_data, cover_image)
                    st.success(f"Book '{title}' added successfully with ID: {book_id}")
    
    elif choice == "View Library":
        st.subheader("Your Library")
        
        df = get_all_books()
        
        if df.empty:
            st.info("Your library is empty. Add some books!")
        else:
            # Display statistics
            total_books = len(df)
            read_books = len(df[df['read_status'] == 'Finished'])
            unread_books = len(df[df['read_status'] == 'Unread'])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Books", total_books)
            col2.metric("Books Read", read_books)
            col3.metric("Books Unread", unread_books)
            
            # Show books in an expandable grid
            st.write("### Book Collection")
            
            for _, row in df.iterrows():
                with st.expander(f"{row['title']} by {row['author']}"):
                    col1, col2 = st.columns([1, 3])
                    
                    # Display cover image if exists
                    cover_path = f"covers/{row['id']}.jpg"
                    if os.path.exists(cover_path):
                        with col1:
                            st.image(cover_path, width=150)
                    
                    with col2:
                        st.write(f"**Author:** {row['author']}")
                        st.write(f"**Genre:** {row['genre']}")
                        st.write(f"**Year:** {row['year']}")
                        st.write(f"**Pages:** {row['pages']}")
                        st.write(f"**Status:** {row['read_status']}")
                        st.write(f"**Rating:** {'⭐' * row['rating']}")
                        
                        if st.button(f"Delete {row['title']}", key=f"del_{row['id']}"):
                            delete_book(row['id'])
                            st.experimental_rerun()
    
    elif choice == "Search":
        st.subheader("Search Your Library")
        
        search_by = st.selectbox("Search by", ["title", "author", "genre", "isbn"])
        search_term = st.text_input("Enter search term")
        
        if search_term:
            results = search_books(search_term, search_by)
            
            if results.empty:
                st.warning("No books found matching your search")
            else:
                st.write(f"Found {len(results)} books:")
                
                for _, row in results.iterrows():
                    with st.expander(f"{row['title']} by {row['author']}"):
                        st.write(f"**ISBN:** {row['isbn']}")
                        st.write(f"**Genre:** {row['genre']}")
                        st.write(f"**Status:** {row['read_status']}")
                        st.write(f"**Rating:** {'⭐' * row['rating']}")
                        
                        if st.button(f"Edit {row['title']}", key=f"edit_{row['id']}"):
                            st.session_state['edit_book'] = row['id']
    
    elif choice == "Statistics":
        st.subheader("Library Statistics")
        
        df = get_all_books()
        
        if df.empty:
            st.info("No data to display")
        else:
            # Basic stats
            st.write("### Overview")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Books", len(df))
            col2.metric("Average Rating", round(df['rating'].mean(), 1))
            col3.metric("Total Pages", df['pages'].sum())
            
            # Reading status pie chart
            st.write("### Reading Status")
            status_counts = df['read_status'].value_counts()
            st.bar_chart(status_counts)
            
            # Genre distribution
            st.write("### Genre Distribution")
            genre_counts = df['genre'].value_counts()
            st.bar_chart(genre_counts)
            
            # Ratings distribution
            st.write("### Ratings Distribution")
            rating_counts = df['rating'].value_counts().sort_index()
            st.bar_chart(rating_counts)
    
    elif choice == "About":
        st.subheader("About")
        st.write("""
        **Personal Library Manager**  
        A simple web application to manage your book collection.
        
        Features:
        - Add books with detailed information
       - Browse your complete library
        - Search by various criteria
        - View statistics about your collection
        - Track reading progress
        
        Built with Python and Streamlit.
        """)

if __name__ == "__main__":
    main()