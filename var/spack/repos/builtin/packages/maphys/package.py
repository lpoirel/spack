from spack import *
import os
import subprocess
import platform
import sys
import spack
from shutil import copyfile

class Maphys(Package):
    """a Massively Parallel Hybrid Solver."""
    homepage = "https://project.inria.fr/maphys/"

    version('0.9.3', 'f52ff32079991163c8905307ce8b8a79',
            url='http://maphys.gforge.inria.fr/maphys_0.9.3.tar.gz')

    svnroot  = "https://scm.gforge.inria.fr/anonscm/svn/maphys/"
    version('svn-maphys-dev',
            svn=svnroot+"branches/maphys-dev")

    pkg_dir = spack.repo.dirname_for_package_name("fake")
    version('exist', '7b878b76545ef9ddb6f2b61d4c4be833',
        url = "file:"+join_path(pkg_dir, "empty.tar.gz"))
    version('src')

    variant('debug', default=False, description='Enable debug symbols')
    variant('blasmt', default=False, description='Enable to use MPI+Threads version of MaPHyS, a multithreaded Blas/Lapack library is required (MKL, ESSL, OpenBLAS)')
    variant('mumps', default=True, description='Enable MUMPS direct solver')
    variant('pastix', default=True, description='Enable PASTIX direct solver')
    variant('examples', default=True, description='Enable compilation and installation of example executables')

    depends_on("mpi")
    depends_on("hwloc")
    depends_on("scotch+mpi+esmumps", when='+mumps')
    depends_on("scotch+mpi~esmumps", when='~mumps')
    depends_on("blas")
    depends_on("lapack")
    depends_on("pastix+mpi", when='+pastix')
    depends_on("pastix+mpi+blasmt", when='+pastix+blasmt')
    depends_on("mumps+mpi", when='+mumps')
    depends_on("mumps+mpi+blasmt", when='+mumps+blasmt')

    def setup(self):
        spec = self.spec

        copyfile('Makefile.inc.example', 'Makefile.inc')
        mf = FileFilter('Makefile.inc')

        mf.filter('prefix := /usr/local', 'prefix := %s' % spec.prefix)

        mpi = spec['mpi'].prefix
        try:
            mpicc = spec['mpi'].mpicc
        except AttributeError:
            mpicc = 'mpicc'
        try:
            mpif90 = spec['mpi'].mpifc
        except AttributeError:
            mpif90 = 'mpif90'
        try:
            mpif77 = spec['mpi'].mpif77
        except AttributeError:
            mpif77 = 'mpif77'

        if spec.satisfies("%intel"):
            mpif90_add_flags = ""
        else:
            mpif90_add_flags = "-ffree-form -ffree-line-length-0"

        mf.filter('MPIFC := mpif90', 'MPIFC := %s -I%s %s' % ( mpif90, mpi.include, mpif90_add_flags) )
        mf.filter('MPICC := mpicc', 'MPICC := %s -I%s' % ( mpicc, mpi.include) )
        mf.filter('MPIF77 := mpif77', 'MPIF77 := %s -I%s' % ( mpif77, mpi.include) )

        if spec.satisfies('+mumps'):
            mumps = spec['mumps'].mumpsprefix
            mumps_libs = spec['mumps'].fc_link
            if spec.satisfies('^mumps+metis'):
                # metis
                mumps_libs += ' '+spec['metis'].cc_link
            if spec.satisfies('^mumps+parmetis'):
                # parmetis
                mumps_libs += ' '+spec['parmetis'].cc_link
            if spec.satisfies('^mumps+scotch'):
                # scotch and ptscotch
                mumps_libs += ' '+spec['scotch'].cc_link
            if spec.satisfies('^mumps+mpi'):
                # scalapack, blacs
                mumps_libs += ' %s %s' % (spec['scalapack'].cc_link, spec['blacs'].cc_link)
            if spec.satisfies('^mumps+blasmt'):
                # lapack and blas
                if '^mkl' in spec or '^essl' in spec:
                    mumps_libs += ' %s' % spec['lapack'].fc_link_mt
                else:
                    mumps_libs += ' %s' % spec['lapack'].fc_link
                mumps_libs += ' %s' % spec['blas'].fc_link_mt
            else:
                mumps_libs += ' %s %s' % (spec['lapack'].fc_link, spec['blas'].fc_link)
            mf.filter('^MUMPS_prefix  :=.*',
                      'MUMPS_prefix  := %s' % mumps)
            mf.filter('^MUMPS_LIBS :=.*',
                      'MUMPS_LIBS := %s' % mumps_libs)
            if not spec.satisfies('^mumps+scotch'):
                mf.filter('^MUMPS_FCFLAGS \+= -DLIBMUMPS_USE_LIBSCOTCH',
                          '#MUMPS_FCFLAGS += -DLIBMUMPS_USE_LIBSCOTCH')
        else:
            mf.filter('^MUMPS_prefix  :=.*',
                      '#MUMPS_prefix  := version without mumps')
            mf.filter('^MUMPS_LIBS :=.*',
                      'MUMPS_LIBS  :=')
            mf.filter('^MUMPS_FCFLAGS  :=.*',
                      'MUMPS_FCFLAGS  := ')
            mf.filter('^MUMPS_FCFLAGS \+=  -I\$\{MUMPS_prefix\}/include',
                      '#MUMPS_FCFLAGS += -I${MUMPS_prefix}/include')
            mf.filter('^MUMPS_FCFLAGS \+= -DLIBMUMPS_USE_LIBSCOTCH',
                      '#MUMPS_FCFLAGS += -DLIBMUMPS_USE_LIBSCOTCH')

        if spec.satisfies('+pastix'):
            pastix = spec['pastix'].prefix
            mf.filter('PASTIX_topdir := \$\(3rdpartyPREFIX\)/pastix/32bits',
                      'PASTIX_topdir := %s' % pastix)
            pastix_libs=subprocess.Popen([pastix+"/bin/pastix-conf", "--libs"], stdout=subprocess.PIPE).communicate()[0]
            mf.filter('PASTIX_FCFLAGS := -DHAVE_LIBPASTIX -I\$\{PASTIX_topdir\}/install',
                      'PASTIX_FCFLAGS := -DHAVE_LIBPASTIX -I${PASTIX_topdir}/include')
            mf.filter('PASTIX_LIBS := -L\$\{PASTIX_topdir\}/install -lpastix -lrt',
                      'PASTIX_LIBS := %s ' % pastix_libs)
        else:
            mf.filter('PASTIX_topdir := \$\(3rdpartyPREFIX\)/pastix/32bits',
                      '#PASTIX_topdir := %s')
            mf.filter('PASTIX_FCFLAGS := -DHAVE_LIBPASTIX -I\$\{PASTIX_topdir\}/install',
                      '#PASTIX_FCFLAGS := -DHAVE_LIBPASTIX -I${PASTIX_topdir}/include')
            mf.filter('PASTIX_LIBS := -L\$\{PASTIX_topdir\}/install -lpastix -lrt',
                      '#PASTIX_LIBS :=')

        if spec.satisfies('~mumps') and spec.satisfies('~pastix'):
            raise RuntimeError('Maphys depends at least on one direct solver, please enable +mumps or +pastix.')

        mf.filter('^METIS_topdir.*',
                  '#METIS_topdir  := version without metis')
        mf.filter('^METIS_CFLAGS.*',
                  'METIS_CFLAGS := ')
        mf.filter('^METIS_FCFLAGS.*',
                  'METIS_FCFLAGS := ')
        mf.filter('^METIS_LIBS.*',
                  'METIS_LIBS := ')

        scotch = spec['scotch'].prefix
        scotch_libs = spec['scotch'].cc_link
        mf.filter('^SCOTCH_prefix.*',
                  'SCOTCH_prefix := %s' % scotch)
        mf.filter('^SCOTCH_LIBS.*',
                  'SCOTCH_LIBS := %s' % scotch_libs)
        mf.filter('SCOTCH_LIBS +=  -lesmumps','')

        blas = spec['blas'].prefix
        lapack = spec['lapack'].prefix
        if spec.satisfies('+blasmt'):
            mf.filter('# THREAD_FCFLAGS \+= -DMULTITHREAD_VERSION -openmp',
                      'THREAD_FCFLAGS += -DMULTITHREAD_VERSION -fopenmp')
            mf.filter('# THREAD_LDFLAGS := -openmp',
                      'THREAD_LDFLAGS := -fopenmp')
            if '^mkl' in spec or '^essl' in spec or '^openblas+mt' in spec:
                blas_libs = spec['blas'].fc_link_mt
            else:
                raise RuntimeError('Only ^openblas+mt, ^mkl and ^essl provide multithreaded blas.')
            if '^mkl' in spec or '^essl' in spec:
                lapack_libs = spec['lapack'].fc_link_mt
            else:
                raise RuntimeError('Only ^mkl and ^essl provide multithreaded lapack.')
        else:
            blas_libs = spec['blas'].fc_link
            lapack_libs = spec['lapack'].fc_link
        if '^mkl' in spec:
            mf.filter('^LMKLPATH   :=.*',
                      'LMKLPATH   := %s' % blas.lib)
        mf.filter('^DALGEBRA_PARALLEL_LIBS  :=.*',
                  'DALGEBRA_PARALLEL_LIBS  := %s %s'  % (lapack_libs, blas_libs) )
        mf.filter('^DALGEBRA_SEQUENTIAL_LIBS :=.*',
                  'DALGEBRA_SEQUENTIAL_LIBS := %s %s' % (lapack_libs, blas_libs) )

        fflags = ''
        cflags = ''
        if spec.satisfies('+debug'):
            fflags += ' -g3 -O0 -Wall -fbounds-check -fbacktrace'
            cflags += ' -g3 -O0 -Wall -fbounds-check -fbacktrace'
        else:
            fflags += ' -O3'
            cflags += ' -O3'
        if '^mkl' in spec:
            fflags += ' -m64 -I${MKLROOT}/include'
            cflags += ' -m64 -I${MKLROOT}/include'
            mf.filter('COMPIL_CFLAGS := -DAdd_',
                      'COMPIL_CFLAGS := -DAdd_ -m64 -I${MKLROOT}/include')

        mf.filter('^FFLAGS :=.*',
                  'FFLAGS := %s' % fflags)
        mf.filter('^FCFLAGS :=.*',
                  'FCFLAGS := %s' % cflags)

        hwloc = spec['hwloc'].prefix
        mf.filter('HWLOC_prefix := /usr/share',
                  'HWLOC_prefix := %s' % hwloc)

        mf.filter('ALL_FCFLAGS  :=  \$\(FCFLAGS\) -I\$\(abstopsrcdir\)/include -I. \$\(ALGO_FCFLAGS\) \$\(CHECK_FLAGS\)',
                  'ALL_FCFLAGS  := $(FCFLAGS) -I$(abstopsrcdir)/include -I. $(ALGO_FCFLAGS) $(CHECK_FLAGS) $(THREAD_FCFLAGS)')
        mf.filter('THREAD_FCLAGS',
                  'THREAD_LDFLAGS')
        mf.filter('^ALL_LDFLAGS  :=.*',
                  'ALL_LDFLAGS  :=  $(MAPHYS_LIBS) $(THREAD_LDFLAGS) $(DALGEBRA_LIBS) $(PASTIX_LIBS) $(MUMPS_LIBS) $(METIS_LIBS) $(SCOTCH_LIBS) $(HWLOC_LIBS) $(LDFLAGS)')

        if platform.system() == 'Darwin':
            mf.filter('-lrt', '');

    def install(self, spec, prefix):

        self.setup()
        make()
        if spec.satisfies('+examples'):
            make('examples')
        make("install", parallel=False)
        if spec.satisfies('+examples'):
            # examples are not installed by default
            install_tree('examples', prefix + '/examples')

    # to use the existing version available in the environment: MAPHYS_DIR environment variable must be set
    @when('@exist')
    def install(self, spec, prefix):
        os.chdir(self.get_env_dir(self.name.upper()+'_DIR'))
        os.symlink(maphysroot+"/bin", prefix.bin)
        os.symlink(maphysroot+"/include", prefix.include)
        os.symlink(maphysroot+"/lib", prefix.lib)
        if spec.satisfies('+examples'):
            os.symlink(maphysroot+'/examples', prefix + '/examples')
