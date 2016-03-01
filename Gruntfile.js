module.exports = function(grunt) {
  var defaultTasks = [
    'bowercopy',
    'concat',
    'clean'
  ];

  var banner = '/*! <%= pkg.name %> <%= pkg.version %> */\n';

  var contribFiles = [
    // external libraries
    'vendor/js/jquery.js',
    'vendor/js/bootstrap.js',
    'vendor/js/bootstrap-fileinput.js',
    'vendor/js/x-editable.js',
    'vendor/js/wysihtml5.js',
    'vendor/js/x-editable-wysihtml5.js',
    'vendor/js/x-editable-bootstrap-wysihtml5.js'
  ];

  var srcFiles = [
  'assets/js/imageTools.js'
  ];

  var allFiles = contribFiles.concat(srcFiles);

  var cssFiles = [
    'vendor/css/bootstrap.css',
    'vendor/css/bootstrap-fileinput.css',
    'vendor/css/x-editable.css',
    'vendor/css/x-editable-bootstrap-wysihtml5.css',
    'assets/css/visorxml.css'
  ];

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    bowercopy: {
      options: {
        srcPrefix: 'bower_components'
      },
      js: {
        options: {
          destPrefix: 'vendor/js'
        },
        files: {
          'jquery.js': 'jquery/dist/jquery.js',
          'bootstrap.js': 'bootstrap/dist/js/bootstrap.js',
          'bootstrap-fileinput.js': 'bootstrap-fileinput/js/fileinput.js',
          'x-editable.js': 'x-editable/dist/bootstrap3-editable/js/bootstrap-editable.js',
          'wysihtml5.js': 'x-editable/dist/inputs-ext/wysihtml5/wysihtml5.js',

          /*'x-editable-wysihtml5.js': 'x-editable/dist/inputs-ext/wysihtml5/bootstrap-wysihtml5-0.0.2/wysihtml5-0.3.0.js',
            This script has been replaced by other with support for base64 images into <img> src attribute.
          */
          'x-editable-wysihtml5.js':'../assets/js/wysihtml5-base64.js',


          'x-editable-bootstrap-wysihtml5.js': 'x-editable/dist/inputs-ext/wysihtml5/bootstrap-wysihtml5-0.0.2/bootstrap-wysihtml5-0.0.2.js'
        }
      },
      css: {
        options: {
          destPrefix: 'vendor/css'
        },
        files: {
          'bootstrap.css': 'bootstrap/dist/css/bootstrap.css',
          'bootstrap-fileinput.css': 'bootstrap-fileinput/css/fileinput.css',
          'x-editable.css': 'x-editable/dist/bootstrap3-editable/css/bootstrap-editable.css',
          'x-editable-bootstrap-wysihtml5.css': 'x-editable/dist/inputs-ext/wysihtml5/bootstrap-wysihtml5-0.0.2/bootstrap-wysihtml5-0.0.2.css'
        }
      },
      fonts: {
        options: {
          destPrefix: 'visorxml/static/fonts'
        },
        files: {
          'glyphicons-halflings-regular.eot': 'bootstrap/dist/fonts/glyphicons-halflings-regular.eot',
          'glyphicons-halflings-regular.svg': 'bootstrap/dist/fonts/glyphicons-halflings-regular.svg',
          'glyphicons-halflings-regular.ttf': 'bootstrap/dist/fonts/glyphicons-halflings-regular.ttf',
          'glyphicons-halflings-regular.woff': 'bootstrap/dist/fonts/glyphicons-halflings-regular.woff',
          'glyphicons-halflings-regular.woff2': 'bootstrap/dist/fonts/glyphicons-halflings-regular.woff2'
        }
      },
      imgs: {
        options: {
          destPrefix: 'visorxml/static/img'
        },
        files: {
          'loading.gif': 'x-editable/dist/bootstrap3-editable/img/loading.gif',
          'clear.png': 'x-editable/dist/bootstrap3-editable/img/clear.png'
        }
      }
    },

    watch: {
      js: {
        files: [
          'Gruntfile.js',
          'app/**/*.js',
          'po/**/*.po'
        ],
        tasks: defaultTasks
      },
      scss: {
        files: [
          'assets/**/*.css'
        ],
        tasks: defaultTasks
      }
    },

    concat: {
      options: {
        banner: banner
      },
      js: {
        src: allFiles,
        dest: 'visorxml/static/js/<%= pkg.name %>.js'
      },
      css: {
        src: cssFiles,
        dest: 'visorxml/static/css/style.css'
      }
    },

    clean: [
      'vendor'
    ]
  });

  grunt.loadNpmTasks('grunt-bowercopy');
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-watch');

  grunt.registerTask('default', defaultTasks);
};
