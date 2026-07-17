$(function () {
	/*ie文字スムージング*/
/*
	// ブラウザのUA
	var userAgent = window.navigator.userAgent.toLowerCase();
	// IEの判定
	if (userAgent.indexOf('msie') >= 0 || userAgent.indexOf('trident') >= 0) {
		$('body p').css(
			"transform", "rotate(0.05deg)"
		);
		$('h1').css(
			"transform", "rotate(0.05deg)"
		);
		$('h2').css(
			"transform", "rotate(0.05deg)"
		);
		$('h3').css(
			"transform", "rotate(0.05deg)"
		);
		$('h4').css(
			"transform", "rotate(0.05deg)"
		);
		$('h5').css(
			"transform", "rotate(0.05deg)"
		);
		$('a').css(
			"transform", "rotate(0.05deg)"
		);

		$('table').css(
			"transform", "rotate(-0.001deg)"
		);

		$('li').css(
			"transform", "rotate(0.05deg)"
		);

		$('iframe').css(
			"transform", "rotate(0.05deg)"
		);

		$('img').css(
			"transform", "none"
		);

		$('ul.bannerArea li').css(
			"transform", "none"
		);

		$('ul.bannerArea li a').css(
			"transform", "none"
		);

		$('.feature ul li').css(
			"transform", "none"
		);

		$('.feature ul li a').css(
			"transform", "none"
		);

                $('select').css(
                        "transform", "rotate(0.05deg)"
                );
	}
*/


	/*ページトップ戻りボタン*/
	$(window).load(function () {
		$('.scBtnBlock').hide();
		posBottomBtn()
	});

	$('.backBtn').click(function () {
		$('body,html').animate({
			scrollTop: 0
		}, 800);
	});

	$(window).scroll(function () {
		posBottomBtn()
	});

	$(window).resize(function () {
		posBottomBtn()
	});

	function posBottomBtn() {
		var stop_pos = $('footer').offset().top;
		var footer_h = $('footer').innerHeight();
		var page_h = $('body').innerHeight();
		var scroll_y = $(window).scrollTop(); //スクロール量
		var add_y = scroll_y + window.innerHeight - stop_pos +10;

		if (scroll_y > 0) {
			$('.backBtn').fadeIn();
		} else {
			$('.backBtn').fadeOut();
		}

		if (scroll_y + $(window).height() > stop_pos) {
			$('.backBtn').css({
				'bottom': add_y + "px"
			});
		} else {
			$('.backBtn').css({
				'bottom': "10px"
			});
		}
	}

	/*ヘッダ検索窓*/
	$('.searchBox').focusin(function () {
			$('.topSearch').addClass("focus")
	});
	$('.searchBox').focusout(function () {
		$('.topSearch').removeClass("focus")
	});


	/*サブメニューアクティブ判定*/
	$(window).load(function () {
		var url=window.location;
		var path= url.href.split('/');
		var page_name = path.pop().replace(".html", "");
		var page_dir = path[path.length-1];

		$('.subMenu ul li').each(function () {
			var active_id = $(this).find('a').attr('id');

			if(page_name.indexOf(active_id)!==-1 || page_dir.indexOf(active_id)!==-1){
				$(this).find('a').addClass('active')
			}else{
				$(this).find('a').removeClass('active')
			}

		});
	});

	/*追従バナー位置*/
	if($('.scrollBanner').css('display')=="block"){
		$(window).scroll(function () {
			posScrollBanner();
		});
	}

	function posScrollBanner() {
		var stop_pos = $('footer').offset().top;
		var footer_h = $('footer').innerHeight();
		var page_h = $('body').innerHeight();
		var scroll_y = $(window).scrollTop(); //スクロール量
		var add_y = scroll_y + window.innerHeight - stop_pos +70;

		if (scroll_y + $(window).height() > stop_pos) {
			$('.scrollBanner').css({
				'bottom': add_y + "px"
			});
		} else {
			$('.scrollBanner').css({
				'bottom': "70px"
			});
		}
	}

});

function FixedAnime() {
	var headerH = $('header').outerHeight(true);
	var scroll = $(window).scrollTop();
	if (scroll > headerH){//headerの高さ以上になったら
			$('header').addClass('fixed').removeClass('off');
			$('#mainContainer').addClass('fixed');//fixedというクラス名を付与
			$('.headerInner').addClass('fixed');//fixedというクラス名を付与
			$('.globalNavi').addClass('fixed');//fixedというクラス名を付与
			$('.topSearch').addClass('fixed');//fixedというクラス名を付与
			headerbanner00.src="/KeibaWeb/resources/img/header_banner_00_fixed.png?bld=20240319134801"
		}else{//それ以外は
			$('header').addClass('off').removeClass('fixed');
			$('#mainContainer').removeClass('fixed');//fixedというクラス名を付与
			$('.headerInner').removeClass('fixed');//fixedというクラス名を除去
			$('.globalNavi').removeClass('fixed');//fixedというクラス名を除去
			$('.topSearch').removeClass('fixed');//fixedというクラス名を除去
			headerbanner00.src="/KeibaWeb/resources/img/header_banner_00.png?bld=20240319134801"
		}
}
$(window).scroll(function () {
	FixedAnime();/* スクロール途中からヘッダーを出現させる関数を呼ぶ*/
});
$(window).on('load', function () {
	FixedAnime();/* スクロール途中からヘッダーを出現させる関数を呼ぶ*/
});
