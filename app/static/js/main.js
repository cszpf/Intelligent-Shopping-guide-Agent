$(document).ready(function (e) {
    $('#message_box').scrollTop($("#message_box")[0].scrollHeight + 20);
    $('.uname').hover(
        function () {
            $('.managerbox').stop(true, true).slideDown(100);
        },
        function () {
            $('.managerbox').stop(true, true).slideUp(100);
        }
    );


    $('.sub_but').click(function (event) {
        sendMessage(event);
    });

    /*按下按钮或键盘按键*/
    $("#message").keydown(function (event) {
        var e = window.event || event;
        var k = e.keyCode || e.which || e.charCode;
        //按下ctrl+enter发送消息
        if (k == 13) {
            sendMessage(event);
        }
    });

});

var domain = ''

function getDomain(sentence) {
    if (sentence.indexOf('手机') != -1) {
        domain = 'phone';
        return;
    }
    if (sentence.indexOf('电脑') != -1) {
        domain = 'computer';
        return;
    }
    if (sentence.indexOf('相机') != -1) {
        domain = 'camera';
        return;
    }
}

function changeDomainDetail() {
    $("#detail").empty()
    if (domain == 'computer') {
        id_name = {
            'brand': '品牌',
            'memory': '内存',
            'disk': '硬盘',
            'price': '价格',
            'cpu': '处理器',
            'gpu': '显卡'
        }
        for (item in id_name) {
            $("#detail").append("<li>" + id_name[item] + "：<span id=" + item + ">无</span>  </li>")
        }
    }
    if (domain == 'phone') {
        id_name = {
            'brand': '品牌',
            'price': '价格',
            'memory': '机身内存',
            'ram': '运行内存',
            'size': '屏幕大小',
            'backca': '像素'
        }
        for (item in id_name) {
            $("#detail").append("<li>" + id_name[item] + "：<span id=" + item + ">无</span>  </li>")
        }
    }
    if (domain == 'camera') {

    }
}

function setDetail(slot_value) {
    if (domain == 'phone') {
        if (response['brand'] != null)
            $('#brand').text(response['brand']);
        if (response['memory'] != null)
            $('#memory').text(response['memory']);
        if (response['price'] != null)
            $('#price').text(response['price']);
        if (response['ram'] != null)
            $('#ram').text(response['ram']);
        if (response['size'] != null)
            $('#size').text(response['size']);
        if (response['backca'] != null)
            $('#backca').text(response['backca']);
    }
}

function showResult(result) {
    if (domain == 'phone') {
        let domData = $(`<div class="msg_item fn-clear">
        <div class="uface"><img src="{{ url_for('static', filename='images/bot2.jpg')}}" width="40" height="40" alt="" /></div>
        <div class="item_right">
            <table class="table table-striped">
                <tbody>
                    <tr>
                        <td>型号</td>
                        <td>价格</td>
                        <td>后摄像素</td>
                        <td>机身内存</td>
                        <td>运行内存</td>
                        <td>屏幕大小</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>`)
        let insertDom = domData.children('tbody');
        for (res in result) {
            let row = `<tr>
            <td>${res['name']}</td>
            <td>${res['price']}</td>
            <td>${res['backca']}</td>
            <td>${res['memory']}</td>
            <td>${res['ram']}</td>
            <td>${res['size']}</td>
        </tr>`
            insertDom.append(row)
        }
        $('#message_box').append(domData);
    }
}

function sendMessage(evente) {
    var msg = $("#message").val();
    var htmlData = '<div class="msg_item_I fn-clear">' +
        '<div class="uface"><img src="{{ url_for(' + "'static'" + ", filename='images/user.jpg')}}" + ' width="40" height="40"  alt=""/></div>' +
        '   <div class="item_right">' +
        '     <div class="msg ">' + msg + '</div>' +
        '   </div>' +
        '</div>';
    $("#message_box").append(htmlData);
    $('#message_box').scrollTop($("#message_box")[0].scrollHeight + 20);
    $("#message").val('');
    if (domain == '') {
        domain = getDomain(msg);
        changeDomainDetail();
    }
    $.post('/dialog', {
        message: msg,
        domain: domain
    }).done(function (response) {
        var msg_bot = response['response']
        console.log(msg_bot)
        var botHtmlData = '<div class="msg_item fn-clear">' +
            '   <div class="uface"><img src="{{ url_for(' + "'static', filename='images/bot2.jpg')}}" + ' width="40" height="40"  alt=""/></div>' +
            '   <div class="item_right">' +
            '     <div class="msg">' + msg_bot + '</div>' +
            '   </div>' +
            '</div>';
        $("#message_box").append(botHtmlData);
        $('#message_box').scrollTop($("#message_box")[0].scrollHeight + 20);
        // 侧边栏处理
        setDetail(response['slot_value'])
        if (response['showResult']) {
            showResult(response['result'])
        }
    });
}