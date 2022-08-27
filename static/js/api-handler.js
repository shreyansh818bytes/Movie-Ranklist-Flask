// Fetch movie data on submiting a search query
// And reload page on success.
function showLoadingButton(buttonId) {
  const button = document.getElementById(buttonId);
  button.setAttribute("disabled", true);
  button.innerHTML =
    '<i class="fa fa-spinner fa-spin" style="color: white;"></i>';
}

function postSearchRequest(singleInputComponent, multiInputComponent) {
  searchStringsArray = [singleInputComponent.value].concat(
    multiInputComponent.value.split("\n")
  );
  showLoadingButton("submit_btn");
  fetch("/search", {
    method: "POST",
    mode: "cors",
    cache: "no-cache",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      searchStringList: searchStringsArray,
    }),
  })
    .then((response) => response.json())
    .then((response) => {
      if (response.message && response.data?.total) {
        window.location.reload();
      }
    });
}

function postDeleteRequest(movie_id) {
  showLoadingButton(movie_id + "-dlt-btn");
  fetch("/delete", {
    method: "POST",
    mode: "cors",
    cache: "no-cache",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      movieId: movie_id,
    }),
  })
    .then((response) => response.json())
    .then((response) => {
      if (response.message && response.data?.total != undefined) {
        const movie_card = document.getElementById(movie_id);
        movie_card.remove();
        $("#movie-total").text(
          `${response.data.total.toString()} Movies Listed`
        );
      }
    });
}
