// ================= PAGE LOAD =================

document.addEventListener("DOMContentLoaded", () => {

    loadFeaturedBooks();

    document.getElementById("searchBox").addEventListener("keypress", function(event){

        if(event.key === "Enter"){
            searchBooks();
        }

    });

});

// ================= FEATURED BOOKS =================

async function loadFeaturedBooks(){

    document.getElementById("results").innerHTML =
    "<h3 style='text-align:center;'>Loading featured books...</h3>";

    try{

        const response = await fetch("/featured");

        const books = await response.json();

        displayBooks(books,"📚 Featured Books");

    }

    catch(error){

        console.log(error);

    }

}

// ================= SEARCH =================

async function searchBooks(){

    const q=document.getElementById("searchBox").value.trim();

    if(q===""){
        loadFeaturedBooks();
        return;
    }

    document.getElementById("results").innerHTML =
    "<h3 style='text-align:center;'>Searching...</h3>";

    try{

        const response=await fetch("/search?q="+encodeURIComponent(q));

        const books=await response.json();

        if(books.length===0){

            document.getElementById("results").innerHTML =
            "<h3 style='text-align:center;'>No books found.</h3>";

            return;

        }

        displayBooks(books,"🔍 Search Results");

    }

    catch(error){

        console.log(error);

    }

}

// ================= DISPLAY =================

function displayBooks(books,title){

    let html=`<h2 style="text-align:center;margin-bottom:25px;">${title}</h2>`;

    books.forEach(book=>{

        html+=`

        <div class="book">

            <img src="${book.image_url}" alt="Book Cover">

            <h3>${book.title}</h3>

            <p><b>Author:</b><br>${book.author}</p>

            <p><b>Year:</b> ${book.publication_year}</p>

            <a href="/book/${book.isbn}">
    <button>
        View Details
    </button>
</a>

        </div>

        `;

    });

    document.getElementById("results").innerHTML=html;

}

// ================= RECOMMEND =================

async function recommendBook(isbn){

    document.getElementById("results").innerHTML =
    "<h3 style='text-align:center;'>Loading recommendations...</h3>";

    const response=await fetch("/recommend/"+isbn);

    const books=await response.json();

    displayBooks(books,"❤️ Recommended Books");

}