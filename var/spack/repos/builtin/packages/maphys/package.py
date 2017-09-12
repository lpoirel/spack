from spack import *
import os
import subprocess
import platform
import sys
import spack
from shutil import copyfile

def get_submodules():
    git = which('git')
    git('submodule', 'update', '--init', '--recursive')

class Maphys(Package):
    """a Massively Parallel Hybrid Solver."""
    homepage = "http://morse.gforge.inria.fr/maphys/maphys.html"
    svnroot  = "https://scm.gforge.inria.fr/anonscm/svn/maphys/"
    gitroot  = "https://gitlab.inria.fr/solverstack/maphys.git"

    version('master' , git=gitroot, branch='master')
    version('develop', git=gitroot, branch='develop')
    version('0.9.3'  , git=gitroot, branch='release/0.9.3')
    version('cg_modif', git=gitroot, branch='feature/cg_modif')
    version('paddle', git=gitroot, branch='feature/paddle')

    version('0.9.6', '75b1587a17c70740e693c4ffe5d115cc',
            url='http://morse.gforge.inria.fr/maphys/maphys-0.9.6.0.tar.gz', preferred=True)
    version('0.9.6.0', '75b1587a17c70740e693c4ffe5d115cc',
            url='http://morse.gforge.inria.fr/maphys/maphys-0.9.6.0.tar.gz')
    version('0.9.5', '53289def2993d9882e724e3a659cd200',
            url='http://morse.gforge.inria.fr/maphys/maphys-0.9.5.1.tar.gz')
    version('0.9.5.1', '53289def2993d9882e724e3a659cd200',
            url='http://morse.gforge.inria.fr/maphys/maphys-0.9.5.1.tar.gz')
    version('0.9.5.0', '8bc00e6597ef5b780243a794c6f71700',
            url='http://morse.gforge.inria.fr/maphys/maphys-0.9.5.0.tar.gz')
    version('0.9.4.2', 'db6a508e53be2f8f54dc5a46d1043c05',
            url='http://morse.gforge.inria.fr/maphys/maphys-0.9.4.2.tar.gz')
    version('0.9.4.1', 'b735c3fc590239c8f725b46b5e7dd351',
            url='http://morse.gforge.inria.fr/maphys/maphys-0.9.4.1.tar.gz')
    version('0.9.4.0', 'a7d88a78675c97cf98a0c00216b17e43',
            url='http://morse.gforge.inria.fr/maphys/maphys-0.9.4.0.tar.gz')
    version('0.9.4', 'db6a508e53be2f8f54dc5a46d1043c05',
            url='http://morse.gforge.inria.fr/maphys/maphys-0.9.4.2.tar.gz')

    pkg_dir = spack.repo.dirname_for_package_name("fake")
    version('exist', '7b878b76545ef9ddb6f2b61d4c4be833',
        url = "file:"+join_path(pkg_dir, "empty.tar.gz"))
    version('src')

    variant('debug', default=False, description='Enable debug symbols')
    variant('shared', default=True, description='Build MaPHyS as a shared library')
    variant('blasmt', default=False, description='Enable to use MPI+Threads version of MaPHyS, a multithreaded Blas/Lapack library is required (MKL, ESSL, OpenBLAS)')
    variant('mumps', default=True, description='Enable MUMPS direct solver')
    variant('pastix', default=True, description='Enable PASTIX direct solver')
    variant('examples', default=True, description='Enable compilation and installation of example executables')
    variant('fabulous', default=False, description='Enable FABuLOuS iterative solver')
    variant('paddle', default=False, description='Enable Paddle domain decomposer')

    depends_on("cmake")
    depends_on("mpi")
    depends_on("hwloc")
    depends_on("scotch+mpi+esmumps", when='+mumps')
    depends_on("scotch+mpi~esmumps", when='~mumps')
    depends_on("blas")
    depends_on("lapack")
    depends_on("pastix+mpi~metis", when='+pastix')
    depends_on("pastix+mpi+blasmt~metis", when='+pastix+blasmt')
    depends_on("mumps+mpi", when='+mumps')
    depends_on("mumps+mpi+blasmt", when='+mumps+blasmt')
    depends_on('fabulous@ib', when='+fabulous')
    depends_on('paddle', when='+paddle')

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
            pastix_libs=subprocess.Popen([pastix+"/bin/pastix-conf", "--libs"], stdout=subprocess.PIPE).communicate()[0]
            if spec.satisfies('@0.9.3'):
                mf.filter('PASTIX_prefix :=.*',
                          'PASTIX_prefix := %s' % pastix)
                mf.filter('PASTIX_FCFLAGS :=.*',
                          'PASTIX_FCFLAGS := -DHAVE_LIBPASTIX -I${PASTIX_prefix}/include')
                mf.filter('PASTIX_LIBS :=.*','PASTIX_LIBS := %s ' % pastix_libs)
            else:
                mf.filter('PASTIX_topdir := \$\(3rdpartyPREFIX\)/pastix/32bits',
                          'PASTIX_topdir := %s' % pastix)
                mf.filter('PASTIX_FCFLAGS := -DHAVE_LIBPASTIX -I\$\{PASTIX_topdir\}/install',
                      'PASTIX_FCFLAGS := -DHAVE_LIBPASTIX -I${PASTIX_topdir}/include')
                mf.filter('PASTIX_LIBS := -L\$\{PASTIX_topdir\}/install -lpastix -lrt',
                      'PASTIX_LIBS := %s ' % pastix_libs)
        else:
            mf.filter('PASTIX_topdir := \$\(3rdpartyPREFIX\)/pastix/32bits',
                      '#PASTIX_topdir := ')
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

        if spec.satisfies('@0.9.3'):
            mf.filter('DALGEBRA_BLAS_LIBS .*',
                  'DALGEBRA_BLAS_LIBS  := %s %s'  % (lapack_libs, blas_libs) )
            mf.filter('DALGEBRA_SCALAPACK_LIBS .*',
                  'DALGEBRA_PARALLEL_LIBS  :=')
        else:
            mf.filter('^DALGEBRA_PARALLEL_LIBS  :=.*',
                  'DALGEBRA_PARALLEL_LIBS  := %s %s'  % (lapack_libs, blas_libs) )
            mf.filter('^DALGEBRA_SEQUENTIAL_LIBS :=.*',
                  'DALGEBRA_SEQUENTIAL_LIBS := %s %s' % (lapack_libs, blas_libs) )

        fflags = ''
        cflags = ''
        if spec.satisfies('+debug'):
            if spec.satisfies('%gcc'):
                fflags += ' -g3 -O0 -Wall -fcheck=bounds -fbacktrace'
                cflags += ' -g3 -O0 -Wall'
            elif spec.satisfies('%intel'):
                fflags += ' -g3 -O0 -warn all -diag-disable:remark -check bounds -traceback'
                cflags += ' -g3 -O0 -w2'
            else:
                fflags += ' -g -O0'
                cflags += ' -g -O0'
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
        if spec.satisfies('@0.9.3'):
            mf.filter('HWLOC_prefix .*',
                  'HWLOC_prefix := %s' % hwloc)
        else:
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

        if spec.satisfies('@develop') or spec.satisfies('@master') or spec.satisfies('@cg_modif') or spec.satisfies('@paddle'):
            get_submodules()

        # Check if makefile and/or cmake is available
        makefile_avail = False
        cmake_avail = False
        if os.path.isfile("Makefile") and os.path.isfile("Makefile.inc.example"):
            makefile_avail = True
        if os.path.isfile("CMakeLists.txt"):
            cmake_avail = True

        if spec.satisfies('@0.9.4.0'): #cmake not working for this version
            cmake_avail = False

        if cmake_avail:
            # CMake version is now available on the trunk branch
            with working_dir('spack-build', create=True):
                cmake_args = [".."]
                cmake_args.extend(std_cmake_args)
                cmake_args.extend([
                    "-Wno-dev",
                    "-DCMAKE_COLOR_MAKEFILE:BOOL=ON",
                    "-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON"])

                if spec.satisfies('+shared'):
                    # Enable build shared libs.
                    cmake_args.extend(["-DBUILD_SHARED_LIBS=ON"])

                if spec.satisfies('+debug'):
                    # Enable Debug here.
                    cmake_args.extend(["-DCMAKE_BUILD_TYPE=Debug"])
                    if spec.satisfies('@0.9.4'):
                        if spec.satisfies('%gcc'):
                            cflags = '-g3 -O0 -Wall'
                            fflags = '-g3 -O0 -Wall -fcheck=bounds -fbacktrace'
                        elif spec.satisfies('%intel'):
                            cflags = '-g -O0 -w3 -diag-disable:remark'
                            fflags = '-g -O0 -warn all -check bounds -traceback'
                        else:
                            cflags = '-g -O0'
                            fflags = '-g -O0'
                        cmake_args.extend(["-DCMAKE_C_FLAGS=%s" % cflags])
                        cmake_args.extend(["-DCMAKE_Fortran_FLAGS=%s" % fflags])

                else:
                    cmake_args.extend(["-DCMAKE_BUILD_TYPE=Release"])

                if spec.satisfies('+examples'):
                    cmake_args.extend(["-DMAPHYS_BUILD_EXAMPLES=ON"])
                    cmake_args.extend(["-DMAPHYS_BUILD_TESTS=ON"])
                else:
                    cmake_args.extend(["-DMAPHYS_BUILD_EXAMPLES=OFF"])
                    cmake_args.extend(["-DMAPHYS_BUILD_TESTS=OFF"])

                if spec.satisfies('~mumps'):
                    cmake_args.extend(["-DMAPHYS_SDS_MUMPS=OFF"])

                if spec.satisfies('~pastix'):
                    cmake_args.extend(["-DMAPHYS_SDS_PASTIX=OFF"])

                blas_libs = spec['blas'].cc_link
                if spec.satisfies('+blasmt'):
                    cmake_args.extend(["-DMAPHYS_BLASMT=ON"])
                    if '^mkl' in spec or '^essl' in spec or '^openblas+mt' in spec:
                        blas_libs = spec['blas'].fc_link_mt
                    else:
                        raise RuntimeError('Only ^openblas+mt, ^mkl and ^essl provide multithreaded blas.')
                cmake_args.extend(["-DBLAS_LIBRARIES=%s" % blas_libs])
                try:
                    blas_flags = spec['blas'].cc_flags
                except AttributeError:
                    blas_flags = ''
                cmake_args.extend(['-DBLAS_COMPILER_FLAGS=%s' % blas_flags])

                lapack_libs = spec['lapack'].cc_link
                if spec.satisfies('+blasmt'):
                    if '^mkl' in spec:
                        lapack_libs = spec['lapack'].fc_link_mt
                    else:
                        raise RuntimeError('Only ^mkl provide multithreaded lapack.')
                cmake_args.extend(["-DLAPACK_LIBRARIES=%s" % lapack_libs])
                if spec.satisfies('+mumps^mpi'):
                    scalapack_libs = '%s' % (spec['scalapack'].cc_link)
                    cmake_args.extend(["-DSCALAPACK_LIBRARIES=%s" % scalapack_libs])

                if spec.satisfies('+fabulous'):
                    # FABULOUS (IBGMRESDR) (not integrated yet)
                    cmake_args.extend(["-DCMAKE_EXE_LINKER_FLAGS=-lstdc++"])
                    cmake_args.extend(["-DMAPHYS_ITE_IBBGMRESDR=ON"])
                    fabulous_libs = spec['fabulous'].cc_link
                    cmake_args.extend(["-DIBBGMRESDR_LIBRARIES=%s" % fabulous_libs])
                    fabulous_inc = spec['fabulous'].prefix.include
                    cmake_args.extend(["-DIBBGMRESDR_INCLUDE_DIRS=%s" % fabulous_inc])

                if spec.satisfies('+paddle'):
                    cmake_args.extend(["-DMAPHYS_ORDERING_PADDLE=ON"])
                    paddle_lib = spec['paddle'].cc_link
                    paddle_inc = spec['paddle'].cc_flags
                    cmake_args.extend(["-DPADDLE_INCLUDE_DIRS=%s" % paddle_inc])
                    cmake_args.extend(["-DPADDLE_LIBRARIES=%s" % paddle_lib])

                cmake(*cmake_args)
                make()
                make("install")
        elif makefile_avail:
            # Use the Makefile.inc to configure
            self.setup()
            make()
            if spec.satisfies('+examples'):
                make('examples')
            make("install", parallel=False)
            if spec.satisfies('+examples'):
                # examples are not installed by default
                install_tree('examples', prefix + '/examples')
        else:
            raise RuntimeError('Cannot file Makefile or CMake setup ')

    # to use the existing version available in the environment: MAPHYS_DIR environment variable must be set
    @when('@exist')
    def install(self, spec, prefix):
        os.chdir(self.get_env_dir(self.name.upper()+'_DIR'))
        os.symlink(maphysroot+"/bin", prefix.bin)
        os.symlink(maphysroot+"/include", prefix.include)
        os.symlink(maphysroot+"/lib", prefix.lib)
        if spec.satisfies('+examples'):
            os.symlink(maphysroot+'/examples', prefix + '/examples')
