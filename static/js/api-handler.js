// Fetch movie data on submiting a search query
// And reload page on success.
function showLoadingIndicator() {
  $('#submit_btn').prop('disabled', true);
  $('#submit_btn i').attr('class', 'fa fa-spinner fa-spin');
}

function searchPostRequest(singleInputComponent, multiInputComponent, appURL) {
  searchStringsArray = [singleInputComponent.value].concat(
    multiInputComponent.value.split("\n")
  );
  showLoadingIndicator();
  fetch(appURL + "/search", {
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
