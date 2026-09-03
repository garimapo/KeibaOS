$(function () {
  function changePage(year, month) {
    window.location.href = "/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=" + year + "&k_month=" + month;
  }
  $('#selectedYear').on('change', function(e) {
    changePage(e.target.value, $('li.tab.active').attr('month'));
  });
  $('li.tab:not(.active)').on('click', function(e) {
    changePage($('#selectedYear').val(), e.target.getAttribute('month'));
  });
});
//EOF
