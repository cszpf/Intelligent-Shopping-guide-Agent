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
    let  storage=window.localStorage;
    storage['domain'] = '';
    $.get('/resetDialog');
});


function getDomain(){
    let  storage=window.localStorage;
    let domain = storage['domain'];
    if (!domain) return '';
    else return domain;
}

function domainClassifier(sentence) {
    let  storage=window.localStorage;
    if (sentence.indexOf('手机') != -1) {
        storage['domain'] =  'phone';
    }
    if (sentence.indexOf('电脑') != -1) {
        storage['domain'] =  'computer';
    }
    if (sentence.indexOf('相机') != -1) {
        storage['domain'] =  'camera';
    }
}

function changeDomainDetail() {
    $("#detail").empty()
    if (getDomain() == 'computer') {
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
    if (getDomain() == 'phone') {
        id_name = {
            'brand': '品牌',
            'price': '价格',
            'memory': '机身内存',
            'ram': '运行内存',
            'size': '屏幕大小',
            'backca': '像素',
            'experience':'体验属性',
            'function':'配置要求'
        }
        for (item in id_name) {
            $("#detail").append("<li>" + id_name[item] + "：<span id=" + item + ">无</span>  </li>")
        }
    }
    if (getDomain() == 'camera') {

    }
}

function setDetail(slot_value) {
    console.log(slot_value)
    if (getDomain() == 'phone') {
        if (slot_value['name'] != null)
            $('#brand').text(slot_value['brand']);
        if (slot_value['memory'] != null)
            $('#memory').text(slot_value['memory']);
        if (slot_value['price'] != null)
            $('#price').text(slot_value['price']);
        if (slot_value['ram'] != null)
            $('#ram').text(slot_value['ram']);
        if (slot_value['size'] != null)
            $('#size').text(slot_value['size']);
        if (slot_value['backca'] != null)
            $('#backca').text(slot_value['backca']);
        if (slot_value['experience'] != null)
            $('#experience').text(slot_value['experience']);
        if (slot_value['function'] != null){
            let text = slot_value['function'].split(',');
            $('#function').html('<br/>'+text[0]+'<br/>'+text[1]);
        }
    }
    if (getDomain() == 'computer') {
        if (slot_value['brand'] != null)
            $('#brand').text(slot_value['brand']);
        if (slot_value['memory'] != null)
            $('#memory').text(slot_value['memory']);
        if (slot_value['price'] != null)
            $('#price').text(slot_value['price']);
        if (slot_value['disk'] != null)
            $('#disk').text(slot_value['disk']);
        if (slot_value['cpu'] != null)
            $('#cpu').text(slot_value['cpu']);
        if (slot_value['gpu'] != null)
            $('#gpu').text(slot_value['gpu']);
        }
    
}

function showResult(result) {
    console.log(result)
    if (getDomain() == 'phone') {
        let domData = $(`<div class="msg_item fn-clear">
        <div class="uface"><img src='/static/images/bot2.jpg' width="40" height="40" alt="" /></div>
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
        let insertDom = domData.find('tbody');
        console.log(insertDom);
        for (res in result) {
            res = result[res];
            let row = `<tr>
            <td>${res['name']?res['name']:'暂无数据'}</td>
            <td>${res['price']?res['price']+'元':'暂无数据'}</td>
            <td>${res['backca']?res['backca']+'万':'暂无数据'}</td>
            <td>${res['rom']?res['rom']+'GB':'暂无数据'}</td>
            <td>${res['ram']?res['ram']+'GB':'暂无数据'}</td>
            <td>${res['size']?res['size']+'英寸':'暂无数据'}</td>
        </tr>`
            insertDom.append(row)
        }
        $('#message_box').append(domData);
    }
    if (getDomain() == 'computer') {
        let domData = $(`<div class="msg_item fn-clear">
        <div class="uface"><img src='/static/images/bot2.jpg' width="40" height="40" alt="" /></div>
        <div class="item_right">
            <table class="table table-striped">
                <tbody>
                    <tr>
                        <td>品牌</td>
                        <td>价格</td>
                        <td>cpu</td>
                        <td>硬盘大小</td>
                        <td>内存</td>
                        <td>型号</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>`)
        let insertDom = domData.find('tbody');
        console.log(insertDom);
        for (res in result) {
            res = result[res];
            let row = `<tr>
            <td>${res['brand']?res['brand']:'暂无数据'}</td>
            <td>${res['price']?res['price']+'元':'暂无数据'}</td>
            <td>${res['cpu']?res['cpu']:'暂无数据'}</td>
            <td>${res['disk']?res['disk']:'暂无数据'}</td>
            <td>${res['memory']?res['memory']:'暂无数据'}</td>
            <td>${res['name']?res['name']:'暂无数据'}</td>
        </tr>`
            insertDom.append(row)
        }
        $('#message_box').append(domData);
    }
}

function sendMessage(evente) {
    var msg = $("#message").val();
    $("message").text('');
    var htmlData = `<div class="msg_item_I fn-clear">
        <div class="uface">
        <img src="/static/images/user.jpg"
         width="40" height="40"  alt=""/>
         </div>
           <div class="item_right"> 
             <div class="msg ">  ${msg}  </div> 
           </div> 
        </div>`;
    $("#message_box").append(htmlData);
    $('#message_box').scrollTop($("#message_box")[0].scrollHeight + 20);
    $("#message").val('');
    if (getDomain() == '') {
        domainClassifier(msg);
        changeDomainDetail();
    }
    $.get('/dialog', {
        message: msg,
        domain: getDomain()
    }).done(function (response) {
        console.log(response);
        var msg_bot = response['response']
        console.log(msg_bot)
        var botHtmlData = `<div class="msg_item fn-clear"> 
               <div class="uface"><img src="/static/images/bot2.jpg"
             width="40" height="40"  alt=""/></div>
               <div class="item_right"> 
                 <div class="msg">  ${msg_bot}  </div> 
               </div> 
            </div>`;
        $("#message_box").append(botHtmlData);
        $('#message_box').scrollTop($("#message_box")[0].scrollHeight + 20);
        // 侧边栏处理
        setDetail(response['slot_value'])
        if (response['showResult']) {
            showResult(response['result']);
            $('#message_box').scrollTop($("#message_box")[0].scrollHeight + 20);
        }
    });
}