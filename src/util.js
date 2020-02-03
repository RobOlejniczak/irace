function newDiv(id) {
  var div = document.createElement("div");
  div.id = id;
  if (arguments.length > 1) {
    for (var i = 1; i < arguments.length; i++) {
      div.classList.add(arguments[i]);
    }
  }
  return div;
}

function titleDiv(title) {
  var titleDiv = newDiv("div", "center", "large");
  var titleP = document.createElement("p");
  titleP.innerHTML = title;
  titleDiv.appendChild(titleP);
  return titleDiv;
}

function contain(content) {
  var container = document.createElement("div");
  container.classList.add("container");
  if (content != null) {
    container.appendChild(content);
  }
  return container;
}

function table(id) {
  var table = document.createElement("table");
  table.id = id;
  table.style.width = "100%";
  if (arguments.length > 1) {
    for (var i = 1; i < arguments.length; i++) {
      table.classList.add(arguments[i]);
    }
  }
  return table;
}

function linked(slug, text) {
  return '<a href="' + slug + '">' + text + "</a>";
}

function h2LeftLink(slug, text) {
  var h2 = document.createElement("h2");
  var p = document.createElement("p");
  p.classList.add("medium");
  p.classList.add("left");
  var a = document.createElement("a");
  a.href = slug;
  a.innerHTML = text;
  p.appendChild(a);
  h2.appendChild(p);
  return h2;
}

function setTitles(title, subTitle, docTitle, state) {
  $("#title")[0].innerHTML = title;

  var subT = $("#subtitle")[0];
  subT.innerHTML = subTitle;

  subT.classList.forEach(function(e) {
    subT.classList.remove(e);
  });

  if (arguments.length > 4) {
    for (var i = 4; i < arguments.length; i++) {
      subT.classList.add(arguments[i]);
    }
  }

  var fullDocTitle = "iRace - " + docTitle
  if (docTitle != null) {
    document.title = fullDocTitle;
  }

  if (state !== false) {
    updateState(state, fullDocTitle);
  }
}
