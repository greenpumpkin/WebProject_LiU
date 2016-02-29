/*
 * Authors:
 * Cindy Najjar
 * Jan Yvonnig
 */

var sizeMinPwd = 6;
var maxSizeMsg = 300;


displayView = function(view) {
	if (localStorage.getItem("token") == null) {
		document.getElementById("page").innerHTML = document.getElementById(view).innerHTML;
	} else {
		document.getElementById("page").innerHTML = document.getElementById("profileview").innerHTML;
        displayInfo();
		keepMsg("mess");
	}
};

window.onload = function() {
	displayView("welcomeview");
};

connectSocket = function() {
    var ws = new WebSocket("ws://" + document.domain + ":5000/socketconnect");

    ws.onopen = function() {
		console.log("CONNECTION TO SERVER : ESTABLISHED.");
		var data = {"email" : localStorage.getItem("email"),"token" : localStorage.getItem("token")};
		ws.send(JSON.stringify(data));
		console.log(JSON.stringify(data));
	};

	ws.onmessage = function(msg) {
		console.log(msg.data);
		message = JSON.parse(msg.data);
		if (message.success == false) {
			console.log("You are already logged in, in another browser");
            logOut();
		}
	};

    ws.onbeforeunload = function() {
        ws.close();
    };

	ws.onclose = function() {
		console.log("CONNECTION TO SERVER : FINISHED.");
	};

	ws.onerror = function() {
		console.log("ERROR");
	};
};

/********************** Login, Sign up, Log out **********************/

logIn = function() {

	var username = document.getElementById("emailLog").value;
	var password = document.getElementById("passwordLog").value;
	var params = "emailLog="+username+"&passwordLog="+password;

	if (username != null && password != null) {
		var xmlhttp = new XMLHttpRequest();
		xmlhttp.onreadystatechange = function () {
			if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
				var rep = JSON.parse(xmlhttp.responseText);

				if (rep.success == true) {

                    localStorage.setItem("token", rep.token);
                    localStorage.setItem("email", rep.email);
                    displayView("profileview");
                    connectSocket();
				}
                else {
					displayMsg(rep.message, false, "welcomeview");
				}
			}
		};
		xmlhttp.open("POST", "/signin", true);
		xmlhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
		xmlhttp.send(params);
	}
};

logOut = function() {
	var token = localStorage.getItem("token");
	var params = "token="+token;
    var xmlhttp = new XMLHttpRequest();

    localStorage.removeItem("token");
    localStorage.removeItem("email");
	//to display the welcome page after the user signs out
    displayView("welcomeview");


	xmlhttp.open("POST", "/signout", true);
	xmlhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xmlhttp.send(params);
};

signUp = function() {
	var genderSelected = "male";
	if (document.getElementById("female").selected == true) {genderSelected = "female";}

	var newUser = {
		'email': document.getElementById("emailSign").value,
		'password': document.getElementById("passwordSign").value,
		'firstname': document.getElementById("firstName").value,
		'familyname': document.getElementById("familyName").value,
		'gender': genderSelected,
		'city': document.getElementById("city").value,
		'country': document.getElementById("country").value
	};

	var params = "emailSign="+newUser.email+"&passwordSign="+newUser.password+
			"&firstName="+newUser.firstname+"&familyName="+newUser.familyname+
			"&gender="+newUser.gender+"&city="+newUser.city+"&country="+newUser.country;

	if (!(newUser.password.length < sizeMinPwd) && (newUser.password == document.getElementById("repeatPassword").value)) {
		var xmlhttp = new XMLHttpRequest();
		xmlhttp.onreadystatechange = function() {
			if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
				var rep = JSON.parse(xmlhttp.responseText);
				displayMsgSign(rep.message,true);
			}
		};
		xmlhttp.open("POST","/signup",true);
		xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
		xmlhttp.send(params);
	} else if (newUser.password != document.getElementById("repeatPassword").value) {
        displayMsgSign("Error: both passwords must be identical", false);
	} else if (newUser.password.length < sizeMinPwd) {
        displayMsgSign("Error: password must be at least 6 characters long", false);
	}
};


/********************** Shows an error or a success message **********************/
//message : the message which will be displayed,
//success : boolean (true : info message / false : error message),
//view : in which view the message will be displayed
displayMsg = function(message,success,view) {

	var errFrame = document.getElementById("displayMsg");

	if (view == "profileview") {
		errFrame = document.getElementById("displayMsgProfile");
	}

	errFrame.style.display = "block";
	errFrame.innerHTML = message;
	errFrame.style.backgroundColor = "white";
	
	if (success == false) {
		errFrame.style.border = "1px solid red";
	}
		
	else if (success == true) {
		errFrame.style.border = "1px solid black";
	}

	setTimeout(function () {
		errFrame.style.display = "none";
	}, '3000');

};


/********************** Displays the panel of the tab parameter **********************/
tabClicked = function(tab) {
	if (tab == 'home') {
		document.getElementById("home-panel").style.display = "block";
		document.getElementById("account-panel").style.display = "none";
		document.getElementById("browse-panel").style.display = "none";
	} else if (tab == 'account') {
		document.getElementById("account-panel").style.display = "block";
		document.getElementById("home-panel").style.display = "none";
		document.getElementById("browse-panel").style.display = "none";
	} else if (tab == 'browse') {
		document.getElementById("browse-panel").style.display = "block";
		document.getElementById("account-panel").style.display = "none";
		document.getElementById("home-panel").style.display = "none";
		document.getElementById("userPage").style.display = "none";

		if (document.getElementById("searchForm").style.display == "none") {
			document.getElementById("searchForm").style.display = "block";
			document.getElementById("mailSearch").value = "";
		}
	}
};

/********************** Enables a user to change his password **********************/
changePwd = function() {
	var token = localStorage.getItem("token");
	var oldPassword = document.getElementById("oldPwd").value;
	var newPassword = document.getElementById("chgPwd").value;
    var repPassword = document.getElementById("chgRepPwd").value;
	var params = "token="+token+"&pwd="+oldPassword+"&chgPwd="+newPassword;

	if (newPassword.length >= sizeMinPwd && newPassword==repPassword) {
		var xmlhttp = new XMLHttpRequest();
		xmlhttp.onreadystatechange = function() {
			if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
				var rep = JSON.parse(xmlhttp.responseText);
				if (rep.success == true) {
					displayMsg(rep.message,true,"profileview");
				} else {
					displayMsg(rep.message,false,"profileview");
				}
			}
		};
		xmlhttp.open("POST","/changepassword",true);
		xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
		xmlhttp.send(params);
	} else {
		displayMsg("Error: invalid inputs", false, "profileview");
	}
};

/********************** Displays all the info about the user who is logged in **********************/
displayInfo = function() {
	var token = localStorage.getItem("token");
	var xmlhttp = new XMLHttpRequest();
	xmlhttp.open("GET", "/getuserdatabytoken/"+token, true);
	xmlhttp.send();

	xmlhttp.onreadystatechange = function () {
		if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
			var rep = JSON.parse(xmlhttp.responseText);
			if (rep.success == true) {
				document.getElementById("mail-span").innerHTML = rep.data[0];
				document.getElementById("firstname-span").innerHTML = rep.data[1];
				document.getElementById("familyname-span").innerHTML = rep.data[2];
				document.getElementById("gender-span").innerHTML = rep.data[3];
				document.getElementById("city-span").innerHTML = rep.data[4];
				document.getElementById("country-span").innerHTML = rep.data[5];
			}
		}
	};
};

/********************** Stores the "msg" in the database **********************/
send = function(msg,mail,to) {

	var token = localStorage.getItem("token");

	var xmlhttp = new XMLHttpRequest();
	xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
			var rep = JSON.parse(xmlhttp.responseText);
            if (rep.success == true) {
				document.getElementById(to).value = "";
				displayMsg(rep.message, true, "profileview");
				if (to == "mess") {
					keepMsg("mess");

				} else if (to == "messUser") {
					keepMsg("messUser");
				}
            }
            else {
				displayMsg(rep.message, false, "profileview");
			}
        }
	};

	var params = "message="+msg+"&token="+token+"&email="+mail;
	xmlhttp.open("POST","/postmessage",true);
	xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
	xmlhttp.send(params);

};

/********************** Enables a user to post a message to a wall **********************/
msgOnWall = function(to) {

	var token = localStorage.getItem("token");
	var msg = document.getElementById(to).value;
	var email;

    if ((msg.length <= maxSizeMsg) && (msg.length > 0)) {

		if (to == "mess") {
			email = document.getElementById("mail-span").innerHTML;
		} else if (to == "messUser") {
			email = document.getElementById("mail-span-o").innerHTML;
		}

		var xmlhttp = new XMLHttpRequest();
		xmlhttp.open("GET", "/getuserdatabyemail/" + token + "/" + email, true);
		xmlhttp.send();

		xmlhttp.onreadystatechange = function () {
			if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
				var rep = JSON.parse(xmlhttp.responseText);
				if (rep.success == true) {
					send(msg, email, to);
				} else {
					displayMsg(rep.message, false, "profileview");
				}
			}
		};
	} else {
			displayMsg("Message too short or too long", false, "profileview");
		}
	};

/********************** Updates the wall to
              make sure that the messages will appear within it **********************/
keepMsg = function(to) {

	var token = localStorage.getItem("token");
	var wall;

	if (token != null) {
		var xmlhttp = new XMLHttpRequest();
		if (to == "mess") {
			wall = document.getElementById("wall");
			xmlhttp.open("GET", "/getusermessagesbytoken/" + token, true);
		} else if (to == "messUser") {
			wall = document.getElementById("wallUser")
			var email = document.getElementById("mailSearch").value;
			xmlhttp.open("GET", "/getusermessagesbyemail/" + token + "/" + email, true);
		}

		xmlhttp.send();

		xmlhttp.onreadystatechange = function () {
			if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
				var rep = JSON.parse(xmlhttp.responseText);
				if (rep.success == true) {
					//Removing all the messages ...
					while (wall.firstChild) {
						wall.removeChild(wall.firstChild);
					}
					//...and rewriting them all	to be sure they're all in the wall
					for (j = 0; j < rep.data.length; j++) {
						var para = document.createElement("p");
						var msg = document.createTextNode("'"+rep.data[j][0]+"' written by : "+rep.data[j][1]);
						para.appendChild(msg);
						if (to == "mess") {
                            para.setAttribute("ondragstart", "drag(event)");
							para.setAttribute("draggable", "true");
                            para.setAttribute("id","drag"+j);
                        }
						wall.appendChild(para);
					}
				} else {
					displayMsg(rep.message, false, "profileview");
				}
			}
		};
	} else {
		displayMsg("You are not logged in.", false, "profileview");
	}
};

/********************** Builds the info of an other user **********************/
displayInfoOther = function(email) {
	var token = localStorage.getItem("token");
	var xmlhttp = new XMLHttpRequest();
	xmlhttp.open("GET", "/getuserdatabyemail/"+token+"/"+email, true);
	xmlhttp.send();
	xmlhttp.onreadystatechange = function () {
		if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
			var rep = JSON.parse(xmlhttp.responseText);
			if (rep.success == true) {
				document.getElementById("mail-span-o").innerHTML = rep.data[0];
				document.getElementById("firstname-span-o").innerHTML = rep.data[1];
				document.getElementById("familyname-span-o").innerHTML = rep.data[2];
				document.getElementById("gender-span-o").innerHTML = rep.data[3];
				document.getElementById("city-span-o").innerHTML = rep.data[4];
				document.getElementById("country-span-o").innerHTML = rep.data[5];
			}
		}
	};
};

/********************** Enables to search for another user's wall **********************/
searchSomeone = function() { 
	var token = localStorage.getItem("token");
	var email = document.getElementById("mailSearch").value;
	var xmlhttp = new XMLHttpRequest();
	xmlhttp.open("GET", "/getusermessagesbyemail/"+token+"/"+email, true);
	xmlhttp.send();

	xmlhttp.onreadystatechange = function () {
		if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
			var rep = JSON.parse(xmlhttp.responseText);
			if (rep.success == true) {
				displayInfoOther(email);
				loadUserPage();
			} else {
				displayMsg(rep.message, false, "profileview");
				document.getElementById("searchForm").style.display = "block";
				document.getElementById("userPage").style.display = "none";
			}
		}
	};
};

/********************** Enables to display all the info of another user **********************/
loadUserPage = function() {
	document.getElementById("searchForm").style.display = "none";
	document.getElementById("userPage").style.display = "block";
	keepMsg("messUser");
};

/********************** Displays message near the login form **********************/
displayMsgSign = function(message,success) {

	var	errFrame = document.getElementById("displayMsgSignUp");

	errFrame.style.display = "block";
	errFrame.innerHTML = message;
	errFrame.style.backgroundColor = "white";

	if (success == false) {
		errFrame.style.border = "1px solid red";
	}

	else if (success == true) {
		errFrame.style.border = "1px solid black";
	}

	setTimeout(function () {
		errFrame.style.display = "none";
	}, '3000');

};

/********************** Drag and drop functionality **********************/
drag = function(ev) {
	ev.dataTransfer.setData("text", ev.target.id);
}

drop = function(ev) {
	ev.preventDefault();
	var data = ev.dataTransfer.getData("text");
	ev.target.value = document.getElementById(data).innerHTML;
}

allowDrop = function(ev){
	ev.preventDefault();
};