function randomColorInt() {
  return Math.floor(Math.random() * 255);
}

function asHex(n) {
  return n.toString(16, 2).toUpperCase().padStart(2, "0");
}

function asColorCode(rgb) {
  return "#" + asHex(rgb[0]) + asHex(rgb[1]) + asHex(rgb[2]);
}

function colorDelta(rgb1, rgb2) {
  return Math.abs(rgb1[0] - rgb2[0]) +
         Math.abs(rgb1[1] - rgb2[1]) +
         Math.abs(rgb1[2] - rgb2[2]);
}

function explodeColor(c) {
  return c.split("(")[1].split(")")[0].split(",").map(function (x) {
    return parseInt(x);
  });
}

function contrastingColor(rgb) {
  while (true) {
    var randColor = [randomColorInt(), randomColorInt(), randomColorInt()];
    if (colorDelta(rgb, randColor) > 350) {
      return asColorCode(randColor);
    }
  }
}

function currentBackgroundColor() {
  var currentColor = $("body").css("background-color");
  return explodeColor(currentColor);
}

function randomColor() {
  return asColorCode([randomColorInt(), randomColorInt(), randomColorInt()]);
}
