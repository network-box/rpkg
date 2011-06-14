# cli.py - a cli client class module
#
# Copyright (C) 2011 Red Hat Inc.
# Author(s): Jesse Keating <jkeating@redhat.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import argparse
import sys
import os
import logging
import time
import random
import string
import xmlrpclib
try:
    import brew as koji
except ImportError:
    import koji

class cliClient():
    """This is a client class for rhtpkg clients."""

    def __init__(self, config, name=None):
        """This requires a ConfigParser object

        Name of the app can optionally set, or discovered from exe name
        """

        self.config = config
        self.name = name
        if not name:
            self.name = os.path.basename(sys.argv[0])
        # Property holders, set to none
        self._cmd = None
        self._module = None
        # Setup the base argparser
        self.setup_argparser()
        # Add a subparser
        self.subparsers = self.parser.add_subparsers(title = 'Targets',
                                                 description = 'These are '
                                                 'valid commands you can '
                                                 'ask %s to do' % self.name)
        # Register all the commands
        self.setup_subparsers()

    # Define some properties here, for lazy loading
    @property
    def cmd(self):
        """This is a property for the command attribute"""

        if not self._cmd:
            self.load_cmd()
        return(self._cmd)

    def load_cmd(self):
        """This sets up the cmd object"""

        # Load up the library based on exe name
        site = os.path.basename(sys.argv[0])

        # Set target if we got it as an option
        target = None
        if hasattr(self.args, 'target') and self.args.target:
            target = self.args.target

        # load items from the config file
        items = dict(self.config.items(site, raw=True))

        # Create the cmd object
        self._cmd = self.site.Commands(self.args.path,
                                       items['lookaside'],
                                       items['lookasidehash'],
                                       items['lookaside_cgi'],
                                       items['gitbaseurl'],
                                       items['anongiturl'],
                                       items['branchre'],
                                       items['kojiconfig'],
                                       items['build_client'],
                                       user=self.args.user,
                                       dist=self.args.dist,
                                       target=target)

    # This function loads the extra stuff once we figure out what site
    # we are
    def do_imports(self, site=None):
        """Import extra stuff not needed during build

        site option can be used to specify which library to load
        """

        # We do some imports here to be more flexible
        if not site:
            import pyrpkg
            self.site = pyrpkg
        else:
            try:
                __import__(site)
                self.site = sys.modules[site]
            except ImportError:
                raise Exception('Unknown site %s' % site)

    def setup_argparser(self):
        """Setup the argument parser and register some basic commands."""

        self.parser = argparse.ArgumentParser(prog = self.name,
                                              epilog = 'For detailed help '
                                              'pass --help to a target')
        # Add some basic arguments that should be used by all.
        # Add a config file
        self.parser.add_argument('--config', '-c',
                                 default=None,
                                 help='Specify a config file to use')
        # Allow forcing the dist value
        self.parser.add_argument('--dist', default=None,
                                 help='Override the discovered distribution')
        # Override the  discovered user name
        self.parser.add_argument('--user', default=None,
                                 help='Override the discovered user name')
        # Let the user define a path to work in rather than cwd
        self.parser.add_argument('--path', default=None,
                                 help='Define the directory to work in '
                                 '(defaults to cwd)')
        # Verbosity
        self.parser.add_argument('-v', action = 'store_true',
                                 help = 'Run with verbose debug output')
        self.parser.add_argument('-q', action = 'store_true',
                                 help = 'Run quietly only displaying errors')

    def setup_subparsers(self):
        """Setup basic subparsers that all clients should use"""

        # Setup some basic shared subparsers

        # help command
        self.register_help()

        # Add a common build parser to be used as a parent
        self.register_build_common()

        # Other targets
        self.register_build()
        self.register_chainbuild()
        self.register_clean()
        self.register_clog()
        self.register_clone()
        self.register_commit()
        self.register_compile()
        self.register_diff()
        self.register_gimmespec()
        self.register_giturl()
        self.register_import_srpm()
        self.register_install()
        self.register_lint()
        self.register_local()
        self.register_new()
        self.register_new_sources()
        self.register_patch()
        self.register_prep()
        self.register_pull()
        self.register_push()
        self.register_scratch_build()
        self.register_sources()
        self.register_srpm()
        self.register_switch_branch()
        self.register_tag()
        self.register_unused_patches()
        self.register_upload()
        self.register_verify_files()
        self.register_verrel()

    # All the register functions go here.
    def register_help(self):
        """Register the help command."""

        help_parser = self.subparsers.add_parser('help', help = 'Show usage')
        help_parser.set_defaults(command = lambda args: self.usage())

    def register_build_common(self):
        """Create a common build parser to use in other commands"""

        self.build_parser_common = self.subparsers.add_parser('build_common',
                                                         add_help = False)
        self.build_parser_common.add_argument('--nowait',
                                         action = 'store_true',
                                         default = False,
                                         help = "Don't wait on build")
        self.build_parser_common.add_argument('--target',
                                         default = None,
                                         help = 'Define build target to build '
                                         'into')
        self.build_parser_common.add_argument('--background',
                                         action = 'store_true',
                                         default = False,
                                         help = 'Run the build at a low '
                                         'priority')

    def register_build(self):
        """Register the build target"""

        build_parser = self.subparsers.add_parser('build',
                                         help = 'Request build',
                                         parents = [self.build_parser_common],
                                         description = 'This command \
                                         requests a build of the package \
                                         in the build system.  By default \
                                         it discovers the target to build for \
                                         based on branch data, and uses the \
                                         latest commit as the build source.')
        build_parser.add_argument('--skip-tag', action = 'store_true',
                                  default = False,
                                  help = 'Do not attempt to tag package')
        build_parser.add_argument('--scratch', action = 'store_true',
                                  default = False,
                                  help = 'Perform a scratch build')
        build_parser.add_argument('--srpm',
                                  help = 'Build from an srpm.')
        build_parser.set_defaults(command = self.build)

    def register_chainbuild(self):
        """Register the chain build target"""

        chainbuild_parser = self.subparsers.add_parser('chain-build',
                    help = 'Build current package in order with other packages',
                    parents = [self.build_parser_common],
                    formatter_class=argparse.RawDescriptionHelpFormatter,
                    description = """
Build current package in order with other packages.

example: %(name)s chain-build libwidget libgizmo

The current package is added to the end of the CHAIN list.
Colons (:) can be used in the CHAIN parameter to define groups of
packages.  Packages in any single group will be built in parallel
and all packages in a group must build successfully and populate
the repository before the next group will begin building.

For example:

%(name)s chain-build libwidget libaselib : libgizmo :

will cause libwidget and libaselib to be built in parallel, followed
by libgizmo and then the currect directory package. If no groups are
defined, packages will be built sequentially.""" %
                    {'name': self.name})
        chainbuild_parser.add_argument('package', nargs = '+',
                                       help = 'List the packages and order you '
                                       'want to build in')
        chainbuild_parser.set_defaults(command = self.chainbuild)

    def register_clean(self):
        """Register the clean target"""
        clean_parser = self.subparsers.add_parser('clean',
                                         help = 'Remove untracked files',
                                         description = "This command can be \
                                         used to clean up your working \
                                         directory.  By default it will \
                                         follow .gitignore rules.")
        clean_parser.add_argument('--dry-run', '-n', action = 'store_true',
                                  help = 'Perform a dry-run')
        clean_parser.add_argument('-x', action = 'store_true',
                                  help = 'Do not follow .gitignore rules')
        clean_parser.set_defaults(command = self.clean)

    def register_clog(self):
        """Register the clog target"""

        clog_parser = self.subparsers.add_parser('clog',
                                        help = 'Make a clog file containing '
                                        'top changelog entry',
                                        description = 'This will create a \
                                        file named "clog" that contains the \
                                        latest rpm changelog entry. The \
                                        leading "- " text will be stripped.')
        clog_parser.set_defaults(command = self.clog)

    def register_clone(self):
        """Register the clone target and co alias"""

        clone_parser = self.subparsers.add_parser('clone',
                                         help = 'Clone and checkout a module',
                                         description = 'This command will \
                                         clone the named module from the \
                                         configured repository base URL.  \
                                         By default it will also checkout \
                                         the master branch for your working \
                                         copy.')
        # Allow an old style clone with subdirs for branches
        clone_parser.add_argument('--branches', '-B',
                                  action = 'store_true',
                                  help = 'Do an old style checkout with \
                                  subdirs for branches')
        # provide a convenient way to get to a specific branch
        clone_parser.add_argument('--branch', '-b',
                                  help = 'Check out a specific branch')
        # allow to clone without needing a account on the rht buildsystem
        clone_parser.add_argument('--anonymous', '-a',
                                  action = 'store_true',
                                  help = 'Check out a module anonymously')
        # store the module to be cloned
        clone_parser.add_argument('module', nargs = 1,
                                  help = 'Name of the module to clone')
        clone_parser.set_defaults(command = self.clone)

        # Add an alias for historical reasons
        co_parser = self.subparsers.add_parser('co', parents = [clone_parser],
                                          conflict_handler = 'resolve',
                                          help = 'Alias for clone',
                                          description = 'This command will \
                                          clone the named module from the \
                                          configured repository base URL.  \
                                          By default it will also checkout \
                                          the master branch for your working \
                                          copy.')
        co_parser.set_defaults(command = self.clone)

    def register_commit(self):
        """Register the commit target and ci alias"""

        commit_parser = self.subparsers.add_parser('commit',
                                          help = 'Commit changes',
                                          description = 'This envokes a git \
                                          commit.  All tracked files with \
                                          changes will be committed unless \
                                          a specific file list is provided.  \
                                          $EDITOR will be used to generate a \
                                          changelog message unless one is \
                                          given to the command.  A push \
                                          can be done at the same time.')
        commit_parser.add_argument('-c', '--clog',
                                   default = False,
                                   action = 'store_true',
                                   help = 'Generate the commit message from \
                                   the Changelog section')
        commit_parser.add_argument('-t', '--tag',
                                   default = False,
                                   action = 'store_true',
                                   help = 'Create a tag for this commit')
        commit_parser.add_argument('-m', '--message',
                                   default = None,
                                   help = 'Use the given <msg> as the commit \
                                   message')
        commit_parser.add_argument('-F', '--file',
                                   default = None,
                                   help = 'Take the commit message from the \
                                   given file')
        # allow one to commit /and/ push at the same time.
        commit_parser.add_argument('-p', '--push',
                                   default = False,
                                   action = 'store_true',
                                   help = 'Commit and push as one action')
        # Allow a list of files to be committed instead of everything
        commit_parser.add_argument('files', nargs = '*',
                                   default = [],
                                   help = 'Optional list of specific files to \
                                   commit')
        commit_parser.set_defaults(command = self.commit)

        # Add a ci alias
        ci_parser = self.subparsers.add_parser('ci', parents = [commit_parser],
                                          conflict_handler = 'resolve',
                                          help = 'Alias for commit',
                                          description = 'This envokes a git \
                                          commit.  All tracked files with \
                                          changes will be committed unless \
                                          a specific file list is provided.  \
                                          $EDITOR will be used to generate a \
                                          changelog message unless one is \
                                          given to the command.  A push \
                                          can be done at the same time.')
        ci_parser.set_defaults(command = self.commit)

    def register_compile(self):
        """Register the compile target"""

        compile_parser = self.subparsers.add_parser('compile',
                                       help = 'Local test rpmbuild compile',
                                       description = 'This command calls \
                                       rpmbuild to compile the source.  \
                                       By default the prep and configure \
                                       stages will be done as well, \
                                       unless the short-circuit option \
                                       is used.')
        compile_parser.add_argument('--arch', help = 'Arch to compile for')
        compile_parser.add_argument('--short-circuit', action = 'store_true',
                                    help = 'short-circuit compile')
        compile_parser.set_defaults(command = self.compile)

    def register_diff(self):
        """Register the diff target"""

        diff_parser = self.subparsers.add_parser('diff',
                                        help = 'Show changes between commits, '
                                        'commit and working tree, etc',
                                        description = 'Use git diff to show \
                                        changes that have been made to \
                                        tracked files.  By default cached \
                                        changes (changes that have been git \
                                        added) will not be shown.')
        diff_parser.add_argument('--cached', default = False,
                                 action = 'store_true',
                                 help = 'View staged changes')
        diff_parser.add_argument('files', nargs = '*',
                                 default = [],
                                 help = 'Optionally diff specific files')
        diff_parser.set_defaults(command = self.diff)

    def register_gimmespec(self):
        """Register the gimmespec target"""

        gimmespec_parser = self.subparsers.add_parser('gimmespec',
                                         help = 'Print the spec file name')
        gimmespec_parser.set_defaults(command = self.gimmespec)

    def register_giturl(self):
        """Register the giturl target"""

        giturl_parser = self.subparsers.add_parser('giturl',
                                          help = 'Print the git url for '
                                          'building',
                                          description = 'This will show you \
                                          which git URL would be used in a \
                                          build command.  It uses the git \
                                          hashsum of the HEAD of the current \
                                          branch (which may not be pushed).')
        giturl_parser.set_defaults(command = self.giturl)

    def register_import_srpm(self):
        """Register the import-srpm target"""

        import_srpm_parser = self.subparsers.add_parser('import',
                                               help = 'Import srpm content '
                                               'into a module',
                                               description = 'This will \
                                               extract sources, patches, and \
                                               the spec file from an srpm and \
                                               update the current module \
                                               accordingly.  It will import \
                                               to the current branch by \
                                               default.')
        import_srpm_parser.add_argument('--branch', '-b',
                                        help = 'Branch to import onto',
                                        default = 'devel')
        #import_srpm_parser.add_argument('--create', '-c',
        #                                help = 'Create a new local repo',
        #                                action = 'store_true')
        import_srpm_parser.add_argument('srpm',
                                        help = 'Source rpm to import')
        import_srpm_parser.set_defaults(command = self.import_srpm)

    def register_install(self):
        """Register the install target"""

        install_parser = self.subparsers.add_parser('install',
                                       help = 'Local test rpmbuild install',
                                       description = 'This will call \
                                       rpmbuild to run the install \
                                       section.  All leading sections \
                                       will be processed as well, unless \
                                       the short-circuit option is used.')
        install_parser.add_argument('--arch', help = 'Arch to install for',
                                    default = None)
        install_parser.add_argument('--short-circuit', action = 'store_true',
                                    help = 'short-circuit install',
                                    default = False)
        install_parser.set_defaults(command = self.install)

    def register_lint(self):
        """Register the lint target"""

        lint_parser = self.subparsers.add_parser('lint',
                                            help = 'Run rpmlint against local '
                                            'build output')
        lint_parser.add_argument('--info', '-i',
                                 default = False,
                                 action = 'store_true',
                                 help = 'Display explanations for reported \
                                 messages')
        lint_parser.set_defaults(command = self.lint)

    def register_local(self):
        """Register the local target"""

        local_parser = self.subparsers.add_parser('local',
                                     help = 'Local test rpmbuild binary',
                                     description = 'Locally test run of \
                                     rpmbuild producing binary RPMs. The \
                                     rpmbuild output will be logged into a \
                                     file named \
                                     .build-%{version}-%{release}.log')
        local_parser.add_argument('--arch', help = 'Build for arch')
        # optionally define old style hashsums
        local_parser.add_argument('--md5', action = 'store_true',
                              help = 'Use md5 checksums (for older rpm hosts)')
        local_parser.set_defaults(command = self.local)

    def register_new(self):
        """Register the new target"""

        new_parser = self.subparsers.add_parser('new',
                                       help = 'Diff against last tag',
                                       description = 'This will use git to \
                                       show a diff of all the changes \
                                       (even uncommited changes) since the \
                                       last git tag was applied.')
        new_parser.set_defaults(command = self.new)

    def register_new_sources(self):
        """Register the new-sources target"""

        # Make it part of self to be used later
        self.new_sources_parser = self.subparsers.add_parser('new-sources',
                                              help = 'Upload new source files',
                                              description = 'This will upload \
                                              new source files to the \
                                              lookaside cache and remove \
                                              any existing files.  The \
                                              "sources" and .gitignore file \
                                              will be updated for the new \
                                              file(s).')
        self.new_sources_parser.add_argument('files', nargs = '+')
        self.new_sources_parser.set_defaults(command = self.new_sources,
                                             replace = True)

    def register_patch(self):
        """Register the patch target"""

        patch_parser = self.subparsers.add_parser('patch',
                                             help = 'Create and add a gendiff '
                                             'patch file')
        patch_parser.add_argument('--suffix')
        patch_parser.add_argument('--rediff', action = 'store_true',
                          help = 'Recreate gendiff file retaining comments')
        patch_parser.set_defaults(command = self.patch)

    def register_prep(self):
        """Register the prep target"""

        prep_parser = self.subparsers.add_parser('prep',
                                        help = 'Local test rpmbuild prep',
                                        description = 'Use rpmbuild to "prep" \
                                        the sources (unpack the source \
                                        archive(s) and apply any patches.)')
        prep_parser.add_argument('--arch', help = 'Prep for a specific arch')
        prep_parser.set_defaults(command = self.prep)

    def register_pull(self):
        """Register the pull target"""

        pull_parser = self.subparsers.add_parser('pull',
                                        help = 'Pull changes from remote '
                                        'repository and update working copy.',
                                        description = 'This command uses git \
                                        to fetch remote changes and apply \
                                        them to the current working copy.  A \
                                        rebase option is available which can \
                                        be used to avoid merges.',
                                        epilog = 'See git pull --help for \
                                        more details')
        pull_parser.add_argument('--rebase', action = 'store_true',
                             help = 'Rebase the locally committed changes on \
                             top of the remote changes after fetching.  This \
                             can avoid a merge commit, but does rewrite local \
                             history.')
        pull_parser.add_argument('--no-rebase', action = 'store_true',
                             help = 'Do not rebase, override .git settings to \
                             automatically rebase')
        pull_parser.set_defaults(command = self.pull)

    def register_push(self):
        """Register the push target"""

        push_parser = self.subparsers.add_parser('push',
                                            help = 'Push changes to remote '
                                            'repository')
        push_parser.set_defaults(command = self.push)

    def register_scratch_build(self):
        """Register the scratch-build target"""

        scratch_build_parser = self.subparsers.add_parser('scratch-build',
                                        help = 'Request scratch build',
                                        parents = [self.build_parser_common],
                                        description = 'This command \
                                        will request a scratch build \
                                        of the package.  Without \
                                        providing an srpm, it will \
                                        attempt to build the latest \
                                        commit, which must have been \
                                        pushed.  By default all \
                                        approprate arches will be \
                                        built.')
        scratch_build_parser.add_argument('--arches', nargs = '*',
                                          help = 'Build for specific arches')
        scratch_build_parser.add_argument('--srpm', help='Build from srpm')
        scratch_build_parser.set_defaults(command = self.scratch_build)

    def register_sources(self):
        """Register the sources target"""

        sources_parser = self.subparsers.add_parser('sources',
                                               help = 'Download source files')
        sources_parser.add_argument('--outdir',
                                    default = os.curdir,
                                    help = 'Directory to download files into \
                                    (defaults to pwd)')
        sources_parser.set_defaults(command = self.sources)

    def register_srpm(self):
        """Register the srpm target"""

        srpm_parser = self.subparsers.add_parser('srpm',
                                                 help = 'Create a source rpm')
        # optionally define old style hashsums
        srpm_parser.add_argument('--md5', action = 'store_true',
                                 help = 'Use md5 checksums (for older rpm \
                                 hosts)')
        srpm_parser.set_defaults(command = self.srpm)

    def register_switch_branch(self):
        """Register the switch-branch target"""

        switch_branch_parser = self.subparsers.add_parser('switch-branch',
                                                help = 'Work with branches',
                                                description = 'This command \
                                                can create or switch to a \
                                                local git branch.  It can \
                                                also be used to list the \
                                                existing local and remote \
                                                branches.')
        switch_branch_parser.add_argument('branch',  nargs = '?',
                                          help = 'Switch to or create branch')
        switch_branch_parser.add_argument('-l', '--list',
                                          help = 'List both remote-tracking \
                                          branches and local branches',
                                          action = 'store_true')
        switch_branch_parser.set_defaults(command = self.switch_branch)

    def register_tag(self):
        """Register the tag target"""

        tag_parser = self.subparsers.add_parser('tag',
                                       help = 'Management of git tags',
                                       description = 'This command uses git \
                                       to create, list, or delete tags.')
        tag_parser.add_argument('-f', '--force',
                                default = False,
                                action = 'store_true',
                                help = 'Force the creation of the tag')
        tag_parser.add_argument('-m', '--message',
                                default = None,
                                help = 'Use the given <msg> as the tag \
                                message')
        tag_parser.add_argument('-c', '--clog',
                                default = False,
                                action = 'store_true',
                                help = 'Generate the tag message from the \
                                spec changelog section')
        tag_parser.add_argument('-F', '--file',
                                default = None,
                                help = 'Take the tag message from the given \
                                file')
        tag_parser.add_argument('-l', '--list',
                                default = False,
                                action = 'store_true',
                                help = 'List all tags with a given pattern, \
                                or all if not pattern is given')
        tag_parser.add_argument('-d', '--delete',
                                default = False,
                                action = 'store_true',
                                help = 'Delete a tag')
        tag_parser.add_argument('tag',
                                nargs = '?',
                                default = None,
                                help = 'Name of the tag')
        tag_parser.set_defaults(command = self.tag)

    def register_unused_patches(self):
        """Register the unused-patches target"""

        unused_patches_parser = self.subparsers.add_parser('unused-patches',
                                             help = 'Print list of patches '
                                             'not referenced by name in '
                                             'the specfile')
        unused_patches_parser.set_defaults(command = self.unused_patches)

    def register_upload(self):
        """Register the upload target"""

        upload_parser = self.subparsers.add_parser('upload',
                                          parents = [self.new_sources_parser],
                                          conflict_handler = 'resolve',
                                          help = 'Upload source files',
                                          description = 'This command will \
                                          add a new source archive to the \
                                          lookaside cache.  The sources and \
                                          .gitignore file will be updated \
                                          with the new file(s).')
        upload_parser.set_defaults(command = self.new_sources,
                                   replace = False)

    def register_verify_files(self):
        """Register the verify-files target"""

        verify_files_parser = self.subparsers.add_parser('verify-files',
                                            help='Locally verify %%files '
                                            'section',
                                            description="Locally run \
                                            'rpmbuild -bl' to verify the \
                                            spec file's %files sections. \
                                            This requires a successful run \
                                            of 'rhtpkg compile'")
        verify_files_parser.set_defaults(command = self.verify_files)

    def register_verrel(self):

        verrel_parser = self.subparsers.add_parser('verrel',
                                                   help = 'Print the '
                                                   'name-version-release')
        verrel_parser.set_defaults(command = self.verrel)

    # All the command functions go here
    def usage(self):
        self.parser.print_help()

    def build(self, sets=None):
        # We may have gotten arches by way of scratch build, so handle them
        arches = None
        if hasattr(self.args, 'arches'):
            arches = self.args.arches
        # Place holder for if we build with an uploaded srpm or not
        url = None
        # See if this is a chain or not
        chain = None
        if hasattr(self.args, 'chain'):
            chain = self.args.chain
        # Need to do something with BUILD_FLAGS or KOJI_FLAGS here for compat
        if self.args.target:
            self.cmd._target = self.args.target
        # handle uploading the srpm if we got one
        if hasattr(self.args, 'srpm') and self.args.srpm:
            # Figure out if we want a verbose output or not
            callback = None
            if not self.args.q:
                callback = self._progress_callback
            # define a unique path for this upload.  Stolen from /usr/bin/koji
            uniquepath = 'cli-build/%r.%s' % (time.time(),
                                 ''.join([random.choice(string.ascii_letters)
                                          for i in range(8)]))
            # Should have a try here, not sure what errors we'll get yet though
            self.cmd.koji_upload(self.args.srpm, uniquepath, callback=callback)
            if not self.args.q:
                # print an extra blank line due to callback oddity
                print('')
            url = '%s/%s' % (uniquepath, os.path.basename(self.args.srpm))
        # Should also try this, again not sure what errors to catch
        try:
            task_id = self.cmd.build(self.args.skip_tag, self.args.scratch,
                                     self.args.background, url, chain, arches,
                                     sets)
        except Exception, e:
            self.log.error('Could not initiate build: %s' % e)
            sys.exit(1)
        # Now that we have the task ID we need to deal with it.
        if self.args.nowait:
            # Log out of the koji session
            self.cmd.kojisession.logout()
            return
        # pass info off to our koji task watcher
        try:
            self.cmd.kojisession.logout()
            return self._watch_koji_tasks(self.cmd.kojisession,
                                          [task_id])
        except:
            # We could get an auth error if credentials have expired
            # use exc_info here to get what kind of error this is
            self.log.error('Could not watch build: %s' % sys.exc_info()[0])
            sys.exit(1)

    def chainbuild(self):
        if self.cmd.module_name in self.args.package:
            self.log.error('%s must not be in the chain' %
                           self.cmd.module_name)
            sys.exit(1)
        # make sure we didn't get an empty chain
        if self.args.package == [':']:
            self.log.error('Must provide at least one dependency build')
            sys.exit(1)
        # Break the chain up into sections
        sets = False
        urls = []
        build_set = []
        self.log.debug('Processing chain %s' % ' '.join(self.args.package))
        for component in self.args.package:
            if component == ':':
                # We've hit the end of a set, add the set as a unit to the
                # url list and reset the build_set.
                urls.append(build_set)
                self.log.debug('Created a build set: %s' % ' '.join(build_set))
                build_set = []
                sets = True
            else:
                # Figure out the scm url to build from package name
                try:
                    hash = self.cmd.get_latest_commit(component)
                    url = self.cmd.anongiturl % {'module':
                                                 component} + '#%s' % hash
                except Exception, e:
                    self.log.error('Could not get a build url for %s: %s'
                                   % (component, e))
                    sys.exit(1)
                # If there are no ':' in the chain list, treat each object as an
                # individual chain
                if ':' in self.args.package:
                    build_set.append(url)
                else:
                    urls.append([url])
                    self.log.debug('Created a build set: %s' % url)
        # Take care of the last build set if we have one
        if build_set:
            self.log.debug('Created a build set: %s' % ' '.join(build_set))
            urls.append(build_set)
        # See if we ended in a : making our last build it's own group
        if self.args.package[-1] == ':':
            self.log.debug('Making the last build its own set.')
            urls.append([])
        # pass it off to build
        self.args.chain = urls
        self.args.skip_tag = False
        self.args.scratch = False
        self.build(sets=sets)

    def clean(self):
        dry = False
        useignore = True
        if self.args.dry_run:
            dry = True
        if self.args.x:
            useignore = False
        try:
            return self.cmd.clean(dry, useignore)
        except Exception, e:
            self.log.error('Could not clean: %s' % e)
            sys.exit(1)

    def clog(self):
        try:
            self.cmd.clog()
        except Exception, e:
            self.log.error('Could not generate clog: %s' % e)
            sys.exit(1)

    def clone(self):
        if not self.args.anonymous:
            user = self.user
        try:
            if self.args.branches:
                self.cmd.clone_with_dirs(self.args.module[0],
                                         anon=self.args.anonymous)
            else:
                self.cmd.clone(self.args.module[0], self.args.branch,
                               anon=self.args.anonymous)
        except Exception, e:
            self.log.error('Could not clone: %s' % e)
            sys.exit(1)

    def commit(self):
        if self.args.clog:
            try:
                self.cmd.clog()
            except Exception, e:
                self.log.error('Could not create clog: %s' % e)
                sys.exit(1)
            self.args.file = os.path.abspath(os.path.join(self.args.path,
                                                          'clog'))
        try:
            self.cmd.commit(self.args.message, self.args.file,
                            self.args.files)
        except Exception, e:
            self.log.error('Could not commit: %s' % e)
            sys.exit(1)
        if self.args.tag:
            try:
                tagname = self.cmd.nvr
                self.cmd.add_tag(tagname, True, self.args.message,
                                 self.args.file)
            except Exception, e:
                self.log.error('Could not create a tag: %s' % e)
                sys.exit(1)
        if self.args.push:
            self.push()

    def compile(self):
        arch = None
        short = False
        if self.args.arch:
            arch = self.args.arch
        if self.args.short_circuit:
            short = True
        try:
            self.cmd.compile(arch=arch, short=short)
        except Exception, e:
            self.log.error('Could not compile: %s' % e)
            sys.exit(1)

    def diff(self):
        try:
            self.cmd.diff(self.args.cached, self.args.files)
        except Exception, e:
            self.log.error('Could not diff: %s' % e)
            sys.exit(1)

    def gimmespec(self):
        try:
            print(self.cmd.spec)
        except Exception, e:
            self.log.error('Could not get spec file: %s' % e)
            sys.exit(1)

    def giturl(self):
        try:
            print(self.cmd.giturl())
        except Exception, e:
            self.log.error('Could not get the giturl: %s' % e)
            sys.exit(1)

    def import_srpm(self):
        try:
            uploadfiles = self.cmd.import_srpm(self.args.srpm)
            self.cmd.upload(uploadfiles, replace=True)
        except Exception, e:
            self.log.error('Could not import srpm: %s' % e)
            sys.exit(1)
        try:
            self.cmd.diff(cached=True)
        except Exception, e:
            self.log.error('Could not diff the repo: %s' % e)
            sys.exit(1)
        print('--------------------------------------------')
        print("New content staged and new sources uploaded.")
        print("Commit if happy or revert with: git reset --hard HEAD")

    def install(self):
        try:
            self.cmd.install(arch=self.args.arch,
                             short=self.args.short_circuit)
        except Exception, e:
            self.log.error('Could not install: %s' % e)
            sys.exit(1)

    def lint(self):
        try:
            self.cmd.lint(self.args.info)
        except Exception, e:
            self.log.error('Could not run rpmlint: %s' % e)
            sys.exit(1)

    def local(self):
        try:
            if self.args.md5:
                self.cmd.local(arch=self.args.arch, hashtype='md5')
            else:
                self.cmd.local(arch=self.args.arch)
        except Exception, e:
            self.log.error('Could not build locally: %s' % e)
            sys.exit(1)

    def new(self):
        try:
            print(self.cmd.new())
        except Exception, e:
            self.log.error('Could not get new changes: %s' % e)
            sys.exit(1)

    def new_sources(self):
        # Check to see if the files passed exist
        for file in self.args.files:
            if not os.path.isfile(file):
                self.log.error('Path does not exist or is not a file: %s' %
                               file)
                sys.exit(1)
        try:
            self.cmd.upload(self.args.files, replace=self.args.replace)
        except Exception, e:
            self.log.error('Could not upload new sources: %s' % e)
            sys.exit(1)
        print("Source upload succeeded. Don't forget to commit the \
              sources file")

    def patch(self):
        self.log.warning('Not implimented yet')

    def prep(self):
        try:
            self.cmd.prep(arch=self.args.arch)
        except Exception, e:
            self.log.error('Could not prep: %s' % e)
            sys.exit(1)

    def pull(self):
        try:
            self.cmd.pull(rebase=self.args.rebase,
                          norebase=self.args.no_rebase)
        except Exception, e:
            self.log.error('Could not pull: %s' % e)
            sys.exit(1)

    def push(self):
        try:
            self.cmd.push()
        except Exception, e:
            self.log.error('Could not push: %s' % e)
            sys.exit(1)

    def scratch_build(self):
        # A scratch build is just a build with --scratch
        self.args.scratch = True
        self.args.skip_tag = False
        self.build()

    def sources(self):
        try:
            self.cmd.sources(self.args.outdir)
        except Exception, e:
            self.log.error('Could not download sources: %s' % e)
            sys.exit(1)

    def srpm(self):
        try:
            self.cmd.sources()
            if self.args.md5:
                self.cmd.srpm('md5')
            else:
                self.cmd.srpm()
        except Exception, e:
            self.log.error('Could not make an srpm: %s' % e)
            sys.exit(1)

    def switch_branch(self):
        if self.args.branch:
            try:
                self.cmd.switch_branch(self.args.branch)
            except Exception, e:
                self.log.error('Unable to switch to another branch: %s' % e)
                sys.exit(1)
        else:
            try:
                (locals, remotes) = self.cmd._list_branches()
            except Exception, e:
                self.log.error('Unable to list branches: %s' % e)
                sys.exit(1)
            # This is some ugly stuff here, but trying to emulate
            # the way git branch looks
            locals = ['  %s  ' % branch for branch in locals]
            local_branch = self.cmd.repo.active_branch.name
            locals[locals.index('  %s  ' %
                                local_branch)] = '* %s' % local_branch
            print('Locals:\n%s\nRemotes:\n  %s' %
                  ('\n'.join(locals), '\n  '.join(remotes)))

    def tag(self):
        if self.args.list:
            try:
                self.cmd.list_tag(self.args.tag)
            except Exception, e:
                self.log.error('Could not create a list of the tag: %s' % e)
                sys.exit(1)
        elif self.args.delete:
            try:
                self.cmd.delete_tag(self.args.tag)
            except Exception, e:
                self.log.error('Could not delete tag: %s' % e)
                sys.exit(1)
        else:
            filename = self.args.file
            tagname = self.args.tag
            try:
                if not tagname or self.args.clog:
                    if not tagname:
                        tagname = self.cmd.nvr
                    if self.args.clog:
                        self.cmd.clog()
                        filename = 'clog'
                self.cmd.add_tag(tagname, self.args.force,
                                  self.args.message, filename)
            except Exception, e:
                self.log.error('Could not create a tag: %s' % e)
                sys.exit(1)

    def unused_patches(self):
        try:
            unused = self.cmd.unused_patches()
        except Exception, e:
            self.log.error('Could not get unused patches: %s' % e)
            sys.exit(1)
        print('\n'.join(unused))

    def verify_files(self):
        try:
            self.cmd.verify_files()
        except Exception, e:
            self.log.error('Could not verify %%files list: %s' % e)
            sys.exit(1)

    def verrel(self):
        try:
            print('%s-%s-%s' % (self.cmd.module_name, self.cmd.ver,
                                self.cmd.rel))
        except Exception, e:
            self.log.error('Could not get ver-rel: %s' % e)
            sys.exit(1)

    # Other class stuff goes here
    def _display_tasklist_status(self, tasks):
        free = 0
        open = 0
        failed = 0
        done = 0
        for task_id in tasks.keys():
            status = tasks[task_id].info['state']
            if status == koji.TASK_STATES['FAILED']:
                failed += 1
            elif status == koji.TASK_STATES['CLOSED'] or \
            status == koji.TASK_STATES['CANCELED']:
                done += 1
            elif status == koji.TASK_STATES['OPEN'] or \
            status == koji.TASK_STATES['ASSIGNED']:
                open += 1
            elif status == koji.TASK_STATES['FREE']:
                free += 1
        self.log.info("  %d free  %d open  %d done  %d failed" %
                      (free, open, done, failed))
    
    def _display_task_results(self, tasks):
        for task in [task for task in tasks.values() if task.level == 0]:
            state = task.info['state']
            task_label = task.str()
    
            if state == koji.TASK_STATES['CLOSED']:
                self.log.info('%s completed successfully' % task_label)
            elif state == koji.TASK_STATES['FAILED']:
                self.log.info('%s failed' % task_label)
            elif state == koji.TASK_STATES['CANCELED']:
                self.log.info('%s was canceled' % task_label)
            else:
                # shouldn't happen
                self.log.info('%s has not completed' % task_label)
    
    def _watch_koji_tasks(self, session, tasklist):
        if not tasklist:
            return
        self.log.info('Watching tasks (this may be safely interrupted)...')
        # Place holder for return value
        rv = 0
        try:
            tasks = {}
            for task_id in tasklist:
                tasks[task_id] = TaskWatcher(task_id, session, self.log,
                                             quiet=self.args.q)
            while True:
                all_done = True
                for task_id,task in tasks.items():
                    changed = task.update()
                    if not task.is_done():
                        all_done = False
                    else:
                        if changed:
                            # task is done and state just changed
                            if not self.args.q:
                                self._display_tasklist_status(tasks)
                        if not task.is_success():
                            rv = 1
                    for child in session.getTaskChildren(task_id):
                        child_id = child['id']
                        if not child_id in tasks.keys():
                            tasks[child_id] = TaskWatcher(child_id,
                                                          session,
                                                          self.log,
                                                          task.level + 1,
                                                          quiet=self.args.q)
                            tasks[child_id].update()
                            # If we found new children, go through the list
                            # again, in case they have children also
                            all_done = False
                if all_done:
                    if not self.args.q:
                        print
                        self._display_task_results(tasks)
                    break
    
                time.sleep(1)
        except (KeyboardInterrupt):
            if tasks:
                self.log.info(
    """
Tasks still running. You can continue to watch with the 'brew watch-task' command.
    Running Tasks:
    %s""" % '\n'.join(['%s: %s' % (t.str(), t.display_state(t.info))
                       for t in tasks.values() if not t.is_done()]))
            # /usr/bin/koji considers a ^c while tasks are running to be a
            # non-zero exit.  I don't quite agree, so I comment it out here.
            #rv = 1
        return rv
    
    # Stole these three functions from /usr/bin/koji
    def _format_size(self, size):
        if (size / 1073741824 >= 1):
            return "%0.2f GiB" % (size / 1073741824.0)
        if (size / 1048576 >= 1):
            return "%0.2f MiB" % (size / 1048576.0)
        if (size / 1024 >=1):
            return "%0.2f KiB" % (size / 1024.0)
        return "%0.2f B" % (size)
    
    def _format_secs(self, t):
        h = t / 3600
        t = t % 3600
        m = t / 60
        s = t % 60
        return "%02d:%02d:%02d" % (h, m, s)
    
    def _progress_callback(self, uploaded, total, piece, time, total_time):
        percent_done = float(uploaded)/float(total)
        percent_done_str = "%02d%%" % (percent_done * 100)
        data_done = self._format_size(uploaded)
        elapsed = self._format_secs(total_time)
    
        speed = "- B/sec"
        if (time):
            if (uploaded != total):
                speed = self._format_size(float(piece)/float(time)) + "/sec"
            else:
                speed = self._format_size(float(total)/float(total_time)) + \
                "/sec"
    
        # write formated string and flush
        sys.stdout.write("[% -36s] % 4s % 8s % 10s % 14s\r" %
                         ('='*(int(percent_done*36)),
                          percent_done_str, elapsed, data_done, speed))
        sys.stdout.flush()

    def setupLogging(self, log):
        """Setup the various logging stuff."""

        # Assign the log object to self
        self.log = log

        # Add a log filter class
        class StdoutFilter(logging.Filter):

            def filter(self, record):
                # If the record level is 20 (INFO) or lower, let it through
                return record.levelno <= logging.INFO

        # have to create a filter for the stdout stream to filter out WARN+
        myfilt = StdoutFilter()
        # Simple format
        formatter = logging.Formatter('%(message)s')
        stdouthandler = logging.StreamHandler(sys.stdout)
        stdouthandler.addFilter(myfilt)
        stdouthandler.setFormatter(formatter)
        stderrhandler = logging.StreamHandler()
        stderrhandler.setLevel(logging.WARNING)
        stderrhandler.setFormatter(formatter)
        self.log.addHandler(stdouthandler)
        self.log.addHandler(stderrhandler)

    def parse_cmdline(self, manpage=False):
        """Parse the commandline, optionally make a manpage

        This also sets up self.user
        """

        if  manpage:
            # Generate the man page
            man_page = __import__('%s' % 
                                  os.path.basename(sys.argv[0]).strip('.py'))
            man_page.generate(self.parser, self.subparsers)
            sys.exit(0)
            # no return possible

        # Parse the args
        self.args = self.parser.parse_args()
        if self.args.user:
            self.user = self.args.user
        else:
            self.user = os.getlogin()

# Add a class stolen from /usr/bin/koji to watch tasks
# this was cut/pasted from koji, and then modified for local use.
# The formatting is koji style, not the stile of this file.  Do not use these
# functions as a style guide.
# This is fragile and hopefully will be replaced by a real kojiclient lib.
class TaskWatcher(object):

    def __init__(self,task_id,session,log,level=0,quiet=False):
        self.id = task_id
        self.session = session
        self.info = None
        self.level = level
        self.quiet = quiet
        self.log = log

    #XXX - a bunch of this stuff needs to adapt to different tasks

    def str(self):
        if self.info:
            label = koji.taskLabel(self.info)
            return "%s%d %s" % ('  ' * self.level, self.id, label)
        else:
            return "%s%d" % ('  ' * self.level, self.id)

    def __str__(self):
        return self.str()

    def get_failure(self):
        """Print infomation about task completion"""
        if self.info['state'] != koji.TASK_STATES['FAILED']:
            return ''
        error = None
        try:
            result = self.session.getTaskResult(self.id)
        except (xmlrpclib.Fault,koji.GenericError),e:
            error = e
        if error is None:
            # print "%s: complete" % self.str()
            # We already reported this task as complete in update()
            return ''
        else:
            return '%s: %s' % (error.__class__.__name__, str(error).strip())

    def update(self):
        """Update info and log if needed.  Returns True on state change."""
        if self.is_done():
            # Already done, nothing else to report
            return False
        last = self.info
        self.info = self.session.getTaskInfo(self.id, request=True)
        if self.info is None:
            self.log.error("No such task id: %i" % self.id)
            sys.exit(1)
        state = self.info['state']
        if last:
            #compare and note status changes
            laststate = last['state']
            if laststate != state:
                self.log.info("%s: %s -> %s" % (self.str(),
                                           self.display_state(last),
                                           self.display_state(self.info)))
                return True
            return False
        else:
            # First time we're seeing this task, so just show the current state
            self.log.info("%s: %s" % (self.str(), self.display_state(self.info)))
            return False

    def is_done(self):
        if self.info is None:
            return False
        state = koji.TASK_STATES[self.info['state']]
        return (state in ['CLOSED','CANCELED','FAILED'])

    def is_success(self):
        if self.info is None:
            return False
        state = koji.TASK_STATES[self.info['state']]
        return (state == 'CLOSED')

    def display_state(self, info):
        # We can sometimes be passed a task that is not yet open, but
        # not finished either.  info would be none.
        if not info:
            return 'unknown'
        if info['state'] == koji.TASK_STATES['OPEN']:
            if info['host_id']:
                host = self.session.getHost(info['host_id'])
                return 'open (%s)' % host['name']
            else:
                return 'open'
        elif info['state'] == koji.TASK_STATES['FAILED']:
            return 'FAILED: %s' % self.get_failure()
        else:
            return koji.TASK_STATES[info['state']].lower()

if __name__ == '__main__':
    client = cliClient()
    client._do_imports()
    client.parse_cmdline()

    if not client.args.path:
        try:
            client.args.path=os.getcwd()
        except:
            print('Could not get current path, have you deleted it?')
            sys.exit(1)

    # setup the logger -- This logger will take things of INFO or DEBUG and
    # log it to stdout.  Anything above that (WARN, ERROR, CRITICAL) will go
    # to stderr.  Normal operation will show anything INFO and above.
    # Quiet hides INFO, while Verbose exposes DEBUG.  In all cases WARN or
    # higher are exposed (via stderr).
    log = client.site.log
    client.setupLogging(log)

    if client.args.v:
        log.setLevel(logging.DEBUG)
    elif client.args.q:
        log.setLevel(logging.WARNING)
    else:
        log.setLevel(logging.INFO)

    # Run the necessary command
    try:
        client.args.command()
    except KeyboardInterrupt:
        pass