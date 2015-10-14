/**
 * Place HTML in the parent document, convert CSS styles to fixed computed style declarations, and return HTML.
 * (required for headers/footers, which exist outside of the HTML document, and have trouble getting styling otherwise)
 */
function replaceCssWithComputedStyle(html) {
  return page.evaluate(function(html) {
    var host = document.createElement('div');
    host.setAttribute('style', 'display:none;'); // Silly hack, or PhantomJS will 'blank' the main document for some reason
    host.innerHTML = html;

    // Append to get styling of parent page
    document.body.appendChild(host);

    var elements = host.getElementsByTagName('*');
    // Iterate in reverse order (depth first) so that styles do not impact eachother
    for (var i = elements.length - 1; i >= 0; i--) {
      elements[i].setAttribute('style', window.getComputedStyle(elements[i], null).cssText);
    }

    // Remove from parent page again, so we're clean
    document.body.removeChild(host);
    return host.innerHTML;
  }, html);
}

var page = require('webpage').create(),
  system = require('system'),
  address, output, size;

if (system.args.length < 3 || system.args.length > 5) {
  console.log('Usage: rasterize.js URL filename [paperwidth*paperheight|paperformat] [zoom]');
  console.log('  paper (pdf output) examples: "5in*7.5in", "10cm*20cm", "A4", "Letter"');
  phantom.exit(1);
} else {
  address = system.args[1];
  output = system.args[2];
  page.viewportSize = {width: 600, height: 600};
  if (system.args.length > 3 && system.args[2].substr(-4) === ".pdf") {
    page.paperSize = {
      format: system.args[3],
      orientation: 'portrait',
      margin: {
        top: '1.5cm',
        left: '2cm',
        bottom: '0.8cm',
        right: '1cm'
      },
      footer: {
        height: "0.7cm",
        contents: phantom.callback(function (pageNum, numPages) {
          var env = system.env;
          var html ='<div class="footer"> \
          Fecha <small>(de generación del documento)</small>: ' + env['generation_date'] + '<br> \
          Ref. Catastral: ' + env['reference'] + ' \
          <div class="pages"> \
            Página ' + pageNum + ' de ' + numPages + ' \
          </div> \
        </div>';
          return replaceCssWithComputedStyle(html);
        })
      }
    };
  }
  if (system.args.length > 4) {
    page.zoomFactor = system.args[4];
  }
  page.open(address, function (status) {
    if (status !== 'success') {
      console.log('Unable to load the address!');
      phantom.exit();
    } else {
      window.setTimeout(function () {
        page.render(output);
        phantom.exit();
      }, 200);
    }
  });
}
