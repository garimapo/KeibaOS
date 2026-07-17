$(function () {
  // tab 切り替え
  var $tabListBtn = $("#odd_content .odd_sort li");
  var $contentList = $("#odd_content .odd_list");
  var $horseSelect=$("#odd_content .horse_select");
  var $oddTable=$("#odd_content .odd_ranking")



  $tabListBtn.on("click", function () {
    // 並んでいる順番を保存
    var index = $tabListBtn.index(this);
    var id = $(this).attr('id');
      
    $tabListBtn.removeClass("active");
    $contentList.children("li").removeClass("active");
      
      if(id=="option"){
           // 表示切り替え
    $(this).addClass("active");
    $contentList.children("li").removeClass("active");
    $contentList.children("li").eq(index).addClass("active");
    $horseSelect.addClass("active");
    $oddTable.addClass("none")
      }else{
    // 表示切り替え
    $(this).addClass("active");
    $contentList.children("li").removeClass("active");
    $contentList.children("li").eq(index).addClass("active");
    $horseSelect.removeClass("active");   
    $oddTable.removeClass("none")
          }

  });
    
    


  // 同カテゴリパターン 切り替え
  $("#odd_content .odd_list_item .tableList__select").each(function () {
    var $selectBtn = $(this).children('li');
    var $selectContentsList = $(this).parents('ul.formList').find('li.formList--item');
    var selectBtn_index = $selectBtn.index(this);

    $selectBtn.on("click", function () {
      // 並んでいる順番を保存

      var selectBtn_index = $selectBtn.index(this);
       

      if ($(this).hasClass('active')) {

      } else {
        
        
        if (document.getElementById("oddsFlg").value == 3 || document.getElementById("oddsFlg").value == 7) {
           // $selectContentsList.removeClass("active");

            // 表示切り替え
            $selectContentsList.removeClass("active");
            $selectContentsList.eq(selectBtn_index).addClass("active");
        } else if (document.getElementById("oddsFlg").value == 2) {
            $selectBtn.removeClass("active");
            $selectBtn.eq(selectBtn_index).addClass("active");
        } else {}
      }
      if (document.getElementById("oddsFlg").value == 2 || document.getElementById("oddsFlg").value == 3 || document.getElementById("oddsFlg").value == 7) {
          document.getElementById("fixedFlg").value = selectBtn_index + 1;
      }
    });
  });

  //
  // formごとに処理
  //

  /*
  $("#odd_content .odd_list > li.odd_list_item form").on('change', function () {
  	//var input_arrays = $(this).find('input:checked').serializeArray();
  	//console.log(input_arrays['value']);
  });
  */


  $("#odd_content .odd_list > li.odd_list_item form").each(function () {
    var form_name = $(this).prop("name");

    //全頭 全消処理
    $(this).find('input.all_button').on('click', function () {
      var input_name_target = $(this).parents("tr").find("td input").prop("name");
      //console.log(input_name_target + 'all');

      if ($(this).hasClass("allcheck")) {
        if (input_name_target == input_name_target) {
          $(this).parents("tr").find("td input").prop("checked", true);
        }
      } else if ($(this).hasClass("allreset")) {
        $(this).parents("tr").find("td input[type='checkbox']").prop("checked", false);
      }
    });

    $(this).each(function () {

      $(this).find('input[type="radio"]').on("click", function () {
        var radioNo = $(this).val();
        //console.log(radioNo);

        //同列のセルに変化を加えたい場合
        //(this).parents('table ').find('tr > td input[type="checkbox"]').each(function () {
        //	$(this).parents('table td').removeClass('static_hold');
        //	if (($(this).val()) == radioNo) {
        //		$(this).parents('td').addClass('static_hold');
        //	}
        //);
      });



      $(this).find('input').on('click', function () {
        //最終出力変数
        var total_value = 0;

        //重複
        var input_ab = 0
        input_ac = 0
        input_bc = 0
        input_ac = 0;

        //入力されたものを配列にして保存
        var input_array_a = [];
        var input_array_b = [];
        var input_array_c = [];

        $(this).parents('form').find('input:checked').each(function () {

          //input_array.push($(this).val());

          if ($(this).parents('tr').find('input[name="uma"]').length) {
            //console.log('uma');
            input_array_a.push($(this).val());
            //console.log(input_array_a);
          } else if ($(this).parents('tr').find('input[name="umb"]').length) {
            //console.log('umb');
            input_array_b.push($(this).val());
            //console.log(input_array_b);
          } else if ($(this).parents('tr').find('input[name="umc"]').length) {
            //console.log('umc');
            input_array_c.push($(this).val());
            ///console.log(input_array_c);
          } else if ($(this).parents('tr').find('input[name="uma[]"]').length) {
            //console.log('uma');
            input_array_a.push($(this).val());
            //console.log(input_array_a);
          } else if ($(this).parents('tr').find('input[name="umb[]"]').length) {
            //console.log('umb');
            input_array_b.push($(this).val());
            //console.log(input_array_b);
          } else if ($(this).parents('tr').find('input[name="umc[]"]').length) {
            //console.log('umc');
            input_array_c.push($(this).val());
            ///console.log(input_array_c);
          }
        });

        //
        //パターン判定
        //
        // 1- 1 等、存在しない組み合わせを除外する
        function pattern_tierce_two() {
          //1行目に入力されたものからから組み合わせを生成
          for (let i = 0; i < input_array_a.length; i++) {
            const a_value = input_array_a[i];

            for (let j = 0; j < input_array_b.length; j++) {
              const b_value = input_array_b[j];

              //同じ番号の組み合わせは存在しないのでカウントしない
              if (a_value == b_value) {
                total_value - 1;
              } else {
                total_value++;
              }

              //console.log(a_value + '-' + b_value);
              //console.log(total_value);
            }
          }

          return total_value;
        }

        // ３連単 軸１頭流し
        // nP2 
        function quinella_axis(total_value) {
          //var total_value = input_array_a.length * input_array_b.length * (input_array_b.length - 1);
          //重複の番号は計算に含めない
          //重複のvalカウント
          var input_ab = input_array_a.filter(function (val) {
            return input_array_b.indexOf(val) != -1;
          });

          //パターン計算方法
          var total_value = input_array_a.length * (input_array_b.length - input_ab.length) * (input_array_b.length - input_ab.length - 1);
          return total_value;
        }

        //
        //３連単 フォーメーション
        // 1-2-1 等、存在しない組み合わせを省く
        //
        function pattern_tierce(total_value) {

          for (let i = 0; i < input_array_a.length; i++) {
            const a_value = input_array_a[i];
            //console.log(a_value);

            for (let j = 0; j < input_array_b.length; j++) {
              const b_value = input_array_b[j];
              //同じ数字はカウントしない
              if (a_value == b_value) {

              } else {
                //選ばれていない数字であれば次へ
                for (let k = 0; k < input_array_c.length; k++) {
                  const c_value = input_array_c[k];
                  //同じ数字はカウントしない
                  if (a_value == b_value == c_value) {
                    total_value - 1;
                    //console.log('No count');

                  } else if (a_value == c_value) {
                    total_value - 1;
                    //console.log('No count 2');
                  } else if (b_value == c_value) {
                    total_value - 1;
                    //console.log('No count 3');
                  } else {
                    total_value++;
                    //console.log(' count');
                    //console.log(a_value + '-' + b_value + '-' + c_value);
                  }

                  //console.log(total_value);
                }
              }
            }
          }

          return total_value;
        }

        //
        //複勝式 順番は無視
        //
        function pattern_show(total_value) {

          //重複のvalカウント
          var input_ab = input_array_a.filter(function (val) {
            return input_array_b.indexOf(val) != -1;
          });

          //パターン計算方法
          var total_value = input_array_a.length * input_array_b.length - input_ab.length - input_ab.length * (input_ab.length - 1) / 2;

          return total_value;
        }

        //
        // 三連複
        //
        function pattern_trio(total_value) {

          //重複のvalカウント
          //a b比較
          var input_ab = input_array_a.filter(function (val) {
            return input_array_b.indexOf(val) != -1;
          });

          //a c比較
          var input_ac = input_array_a.filter(function (val) {
            return input_array_c.indexOf(val) != -1;
          });

          //b c比較
          var input_bc = input_array_b.filter(function (val) {
            return input_array_c.indexOf(val) != -1;
          });

          //abc
          var input_abc = input_ab.filter(function (val) {
            return input_ac.indexOf(val) != -1;
          });

          var aa = input_array_a.length,
            bb = input_array_b.length,
            cc = input_array_c.length,
            ab = input_ab.length,
            ac = input_ac.length,
            bc = input_bc.length,
            abc = input_abc.length;

          var oa = aa - ab - ac + abc,
            ob = bb - ab - bc + abc,
            oc = cc - bc - ac + abc,
            oab = ab - abc,
            obc = bc - abc,
            oac = ac - abc,
            oabc = abc;

          //console.log('ab = ' + input_ab.length);
          //console.log('ac = ' + input_ac.length);
          //console.log('bc = ' + input_bc.length);
          //console.log('abc = ' + input_abc);


          //パターン計算方法
          //n(n-1) / 2 or nC2 
          var total_value = oa *
            ((oab + ob) * (obc + oc + oac + oabc) + obc * (oc + oac) + oabc * (obc + oc + oac) + obc * (obc - 1) / 2 + oabc * (oabc - 1) / 2) +
            oab * (ob * (obc + oc + oac + oabc) + obc * (oc + oac + oabc) + oabc * (oc + oac) + obc * (obc - 1) / 2 + oabc * (oabc - 1) / 2) +
            oab * (oab - 1) / 2 * (obc + oc + oac + oabc) + oac * (ob * (obc + oc + oabc) + obc * (oc + oabc) + oc * (oab + oabc) + obc *
              (obc - 1) / 2 + oabc * (oabc - 1) / 2) + oac * (oac - 1) / 2 * (oab + ob + obc + oabc) + oabc * (ob * (obc + oc) + obc * oc + obc * (obc - 1) / 2) +
            oabc * (oabc - 1) / 2 * (ob + obc + oc) + oabc * (oabc - 1) * (oabc - 2) / 6;

          return total_value;

        }

        //box 
        function pattern_box(total_value) {
          //var total_value = input_array_a.length
        }

        //box 一列のみパターン
        function pattern_single(total_value) {
          var total_value = input_array_a.length * (input_array_a.length - 1) * (input_array_a.length - 2);
          return total_value;
        }

        // n(n-1)/2 
        function pattern_single_twin(total_value) {
          var total_value = input_array_a.length * (input_array_a.length - 1) / 2;
          return total_value;
        }

        function cntChk(tgt, cnt){
          if (tgt==1) {
            return input_array_a.length >= cnt;
          } else if (tgt==2) {
            return input_array_b.length >= cnt;
          } else if (tgt==3) {
            return input_array_c.length >= cnt;
          }
        }

        function cntChka(){
          return input_array_a.length >= 1;
        }

        function cntChkb(){
          return input_array_b.length >= 1;
        }

        function cntChkc(){
          return input_array_c.length >= 1;
        }

        function cntChk3(tgt, cnt){
          if (tgt==1) {
            return input_array_a.length >= cnt;
          } else if (tgt==2) {
            return input_array_b.length >= cnt;
          } else if (tgt==3) {
            return input_array_c.length >= cnt;
          }
        }


        //-------------------------------------------------------
        //大本の親要素のidでどの計算方法にするか判別 別パターンや除外はifで
        //-------------------------------------------------------
        var pattern_type = $(this).parents('ul.odd_list').attr('id');

        var isChecked = true;

        if (pattern_type === 'odd_pattern_tierce') {
          //
          //３連単
          //
          var pattern_namber = pattern_tierce(total_value);
          isChecked = cntChk(1,1) && cntChk(2,1) && cntChk(3,1);
          isChecked = cntChka && cntChkb && cntChkc;

          if (form_name === 'quinella_axis_1') {
            //
            // ３連単 軸1頭流し マルチ
            //（相手の馬）×（相手の馬ー１）×３
            //
            var pattern_namber = quinella_axis(total_value) * 3;
            //console.log('quinella_axis_1 = ' + pattern_namber);
            isChecked = cntChk(1,1) && cntChk(2,2);

          } else if (form_name.indexOf('quinella_axis_1_') !== -1) {
            if (document.getElementById("fixedFlg").value == '4') {
                //
                // ３連単 軸1頭流し マルチ
                //（相手の馬）×（相手の馬ー１）×３
                //
                var pattern_namber = quinella_axis(total_value) * 3;
                isChecked = cntChk(1,1) && cntChk(2,2);
            } else {
                //
                // ３連単 軸1頭流し 1着固定 ~ 3着固定
                //
                var pattern_namber = quinella_axis(total_value);
                isChecked = cntChk(1,1) && cntChk(2,2);
            }

            //console.log('quinella_axis' + pattern_namber);

          } else if (form_name === 'quinella_axis_2') {
            //
            //３連単 軸2頭流し マルチ
            //
            var pattern_namber = pattern_tierce(total_value) * 6;

          } else if (form_name.indexOf('quinella_axis_2_') !== -1) {
            //
            //３連単  軸2頭流し 1着固定 ~ 3着固定
            //
            var pattern_namber = pattern_tierce(total_value);

          } else if (form_name.indexOf('box') !== -1) {
            //
            // ３連単 box
            //
            var pattern_namber = pattern_single(total_value);
            isChecked = cntChk(1,3);
          } else {

          }
        } else if (pattern_type === 'odd_pattern_show') {
          //
          //馬連複
          //
          var pattern_namber = pattern_show(total_value);
          isChecked = cntChk(1,1) && cntChk(2,1);

          if (form_name.indexOf('box') !== -1) {
            var pattern_namber = pattern_single_twin(total_value);
            isChecked = cntChk(1,2);

          } else {

          }
        } else if (pattern_type === 'odd_pattern_win') {
          //
          //馬連単
          //
          var pattern_namber = pattern_tierce_two(total_value);
          isChecked = cntChk(1,1) && cntChk(2,1);

          if (form_name === 'wheel') {
            var pattern_namber = pattern_namber * 2;

          } else if (form_name.indexOf('box') !== -1) {
            var pattern_namber = pattern_single_twin(total_value) * 2;
            isChecked = cntChk(1,2);

          } else {

          }
        } else if (pattern_type === 'odd_pattern_wide') {
          //
          // ワイド
          //
          var pattern_namber = pattern_show(total_value);
          isChecked = cntChk(1,1) && cntChk(2,1);

          if (form_name === 'wide_wheel') {
            //
            // ワイド 流し
            //
            var pattern_namber = pattern_tierce_two(total_value);

          } else if (form_name === 'wide_wheel_box') {
            //
            // ワイド ボックス
            //
            var pattern_namber = pattern_single_twin(total_value);
            isChecked = cntChk(1,2);

          } else {

          }
        } else if (pattern_type === 'odd_pattern_trio') {
          //
          // 三連複
          //
          var pattern_namber = pattern_trio(total_value);
          isChecked = cntChk(1,1) && cntChk(2,1) && cntChk(3,1);

          if (form_name === 'trio_axis_1') {
            //
            // 三連複 軸1頭流し 1着固定 ~ 3着固定
            //
            var pattern_namber = quinella_axis(total_value) / 2;
            isChecked = cntChk(1,1) && cntChk(2,2);

          } else if (form_name === 'trio_axis_2') {
            //
            //三連複 軸2頭流し
            //
            var pattern_namber = pattern_trio(total_value);


          } else if (form_name === 'trio_box') {
            //
            //三連複 ボックス
            //
            var pattern_namber = pattern_single(total_value) / 6;
            isChecked = cntChk(1,3);

          } else {

          }
        }

        //パターン数出力
        $(this).parents('table').find(".odd_result .result_input > span").text(pattern_namber);
      });
    });
  });
});
