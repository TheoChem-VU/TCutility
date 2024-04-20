import subprocess as sp
import os

fonts = [
	'calibri',
	'arial',
	'times new roman',
	'helvetica',
]

characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ.,/?<>{}[]+-_=^:; '

script = """
const jsdom = require("jsdom");
const { JSDOM } = jsdom;

global.document = new JSDOM("<html><head></head></html>").window.document;

function getTextWidth(text, font) {
  var canvas = getTextWidth.canvas || (getTextWidth.canvas = global.document.createElement("canvas"));
  var context = canvas.getContext("2d");
  context.font = font;
  var metrics = context.measureText(text);
  return metrics.width;
};

let chars = '[CHARACTERS]';
let fonts = [[FONTS]];
for (let j = 0; j < fonts.length; j++) {
  let font = fonts[j];
  for (let i = 0; i < chars.length; i++) {
    console.log(font.replaceAll(" ", "_") + " " + chars[i] + " " + getTextWidth(chars[i], "1pt " + font));
  }
}
""".replace('[CHARACTERS]', characters).replace('[FONTS]', ", ".join(['"' + font + '"' for font in fonts]))

with open('char_width.js', 'w+') as js_script:
	js_script.write(script)

with open('_char_widths.txt', 'w+') as out:
	for line in sp.check_output(['node', 'char_width.js']).decode().splitlines():
		out.write(line + '\n')

os.remove('char_width.js')
