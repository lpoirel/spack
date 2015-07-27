from spack import *
import os


class NetlibBlas(Package):
    """Netlib reference BLAS"""
    homepage = "http://www.netlib.org/lapack/"
    url      = "http://www.netlib.org/lapack/lapack-3.5.0.tgz"

    version('3.5.0', 'b1d3e3e425b2e44a06760ff173104bdf')

    # virtual dependency
    provides('blas')

    # Doesn't always build correctly in parallel
    parallel = False

    def patch(self):
        os.symlink('make.inc.example', 'make.inc')

        mf = FileFilter('make.inc')
        mf.filter('^FORTRAN.*', 'FORTRAN = f90')
        mf.filter('^LOADER.*',  'LOADER = f90')
        mf.filter('^CC =.*',  'CC = cc')
        spec = self.spec
        if spec.satisfies('%gcc'):
            mf.filter('^OPTS     =.*', 'OPTS     = -O2 -frecursive -fPIC')
            mf.filter('^CFLAGS =.*', 'CFLAGS = -O3 -fPIC')
        if spec.satisfies('%icc'):
            mf.filter('^OPTS     =.*', 'OPTS     = -O2 -shared -fpic')
            mf.filter('^CFLAGS =.*', 'CFLAGS = -O3 -shared -fpic')


    def install(self, spec, prefix):
        make('blaslib')

        # Tests that blas builds correctly
        make('blas_testing')

        # No install provided
        mkdirp(prefix.lib)
        install('librefblas.a', prefix.lib)

        # Blas virtual package should provide blas.a and libblas.a
        with working_dir(prefix.lib):
            symlink('librefblas.a', 'blas.a')
            symlink('librefblas.a', 'libblas.a')
