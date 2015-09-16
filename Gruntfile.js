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
    'vendor/js/bootstrap.js'
  ];

  var srcFiles = [
  ];

  var allFiles = contribFiles.concat(srcFiles);

  var cssFiles = [
    'vendor/css/bootstrap.css',
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
          'bootstrap.js': 'bootstrap/dist/js/bootstrap.js',
          'jquery.js': 'jquery/dist/jquery.js'
        }
      },
      css: {
        options: {
          destPrefix: 'vendor/css'
        },
        files: {
          'bootstrap.css': 'bootstrap/dist/css/bootstrap.css'
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
