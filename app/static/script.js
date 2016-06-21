function setPlayerState(data){
    if(data.active && $('#ps_active').is(':visible')){
        $('#ps_active').hide();
        $('#btn-volume').prop('disabled', false);
        $('#btn-stop').prop('disabled', false);
        $('#input-volume').slider('setValue', parseFloat(data.volume))
    }
    else if (!data.active && $('#ps_active').is(':hidden')){
        $('#ps_active').show();
        $('#btn-volume').prop('disabled', true);
        $('#btn-stop').prop('disabled', true);
    }
    $('#ps_volume').html(data.volume+'%');
    $('#ps_playing').html(data.playing);
}
$('#input-volume').slider({
    formatter: function(value) {
        return value + '%';
    }
});
function statusBarUpdate(url){
    $.getJSON(url, function(data) {setPlayerState(data);});
    setInterval(function(){$.getJSON(url, function(data) {setPlayerState(data);})},1000)
}
