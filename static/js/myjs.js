//  $(document).ready(function() {
//   $(function() {
//     $('#datetimepicker6').datetimepicker();
//     $('#datetimepicker7').datetimepicker({
//       useCurrent: false //Important! See issue #1075
//     });
//     $("#datetimepicker6").on("dp.change", function(e) {
//       $('#datetimepicker7').data("DateTimePicker").minDate(e.date);
//     });
//     $("#datetimepicker7").on("dp.change", function(e) {
//       $('#datetimepicker6').data("DateTimePicker").maxDate(e.date);
//     });
//   });
// });


function error_display(obj)
{
	var error = "<div class='alert alert-warning alert-dismissible fade show' role='alert'>"
				+"<strong></Strong>"+obj.error
				+"<button type='button' class='close' data-dismiss='alert' aria-label='Close'>"
				+"<span aria-hidden='true'>&times;</span>"
				+"</button>"
				+"</div>";
				$('#errorMessages').append(error);
}

function del_error_message()
{
	$('#errorMessages').empty();
}

function visit(url)
{
	window.location.href = url;
}


function event_oper(rid, eid, oper)
{
    var data_1 = {
        'rid': rid,
        'eid': eid,
        'oper': oper,
    };
    if (oper == 'edit')
    {
        url = "/edit?eid="+eid+"&egtype=event";
        window.location.href = url;
    }
    $.ajax({
            url:'/event_operation',
            type: 'POST',
            dataType: 'text',
            data: data_1,
            success: function(data){
                var result = JSON.parse(data);
                if ( result.url == undefined )
                {
                    error_display(result);
                }
                else
                {
                    window.location.href = result.url;
                }
            },
            error: function(data){
                console.log(data)
            }
        });
}


function group_oper(rid, gid, oper)
{
    var data_1 = {
        'rid': rid,
        'gid': gid,
        'oper': oper,
    };
    if (oper == 'edit')
    {
        url = "/edit?gid="+gid+"&egtype=group";
        window.location.href = url;
    }
    $.ajax({
            url:'/group_operation',
            type: 'POST',
            dataType: 'text',
            data: data_1,
            success: function(data){
                var result = JSON.parse(data);
                if ( result.url == undefined )
                {
                    error_display(result);
                }
                else
                {
                    window.location.href = result.url
                }
            },
            error: function(data){
                console.log(data)
            }
        });
}


// function action(actionName, success, error, type, formData){
// 	$.ajax({
// 		url: "../cgi/" + actionName + ".py",
// 		type: type,
// 		dataType: 'text',
// 		data: formData,
// 		success: function(data){
// 			console.log("### " + actionName + " ###");
// 			console.log(data);
// 			console.log("########################");
// 			var obj = eval('(' + data + ')');
// 			if (obj.error == "none"){
// 				success(obj);
// 			}
// 			else if (obj.error == "server"){
// 				serverError(obj);
// 			}
// 			else if (obj.error == "data"){
// 				error(obj);
// 			}
// 		},
// 		error: function(data){
// 			serverError(obj);
// 		}
// 	});
// }











