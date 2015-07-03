from spack import *
import os

class Scalfmm(Package):
    """a software library to simulate N-body interactions using the Fast Multipole Method."""
    homepage = "http://scalfmm-public.gforge.inria.fr/doc/"
    url      = "https://gforge.inria.fr/frs/download.php/file/34672/SCALFMM-1.3-56.tar.gz"

    version('1.3-56', '666ba8fef226630a2c22df8f0f93ff9c')
    version('master', git='https://scm.gforge.inria.fr/anonscm/git/scalfmm-public/scalfmm-public.git')

    #variant('blas', default=False, description='Enable BLAS')
    variant('fftw', default=False, description='Enable FFTW')
    variant('mkl', default=False, description='Use BLAS/LAPACK from the Intel MKL library')
    variant('mpi', default=False, description='Enable MPI')
    variant('starpu', default=False, description='Enable StarPU')

    # Does not compile without blas!
    #depends_on("blas", when='+blas')
    depends_on("blas", when='~mkl')
    depends_on("lapack", when='~mkl')
    depends_on("fftw", when='+fftw')
    depends_on("starpu", when='+starpu')
    depends_on("mpi", when='+mpi')


    def install(self, spec, prefix):

        with working_dir('spack-build', create=True):

            cmake_args = [
                "..",
                "-DBUILD_SHARED_LIBS=ON"]

            cmake_args.extend(["-DSCALFMM_USE_BLAS=ON"])
            # if '+blas' in spec:
            #     # Enable BLAS here.
            #     cmake_args.extend(["-DSCALFMM_USE_BLAS=ON"])
            # else:
            #     # Disable BLAS here.
            #     cmake_args.extend(["-DSCALFMM_USE_BLAS=OFF"])

            if '+fftw' in spec:
                # Enable FFTW here.
                cmake_args.extend(["-DSCALFMM_USE_FFT=ON"])
            else:
                # Disable FFTW here.
                cmake_args.extend(["-DSCALFMM_USE_FFT=OFF"])

            if '+starpu' in spec:
                # Enable STARPU here.
                cmake_args.extend(["-DSCALFMM_USE_STARPU=ON"])
            else:
                # Disable STARPU here.
                cmake_args.extend(["-DSCALFMM_USE_STARPU=OFF"])

            if '+mpi' in spec:
                # Enable MPI here.
                cmake_args.extend(["-DSCALFMM_USE_MPI=ON"])
            else:
                # Disable MPI here.
                cmake_args.extend(["-DSCALFMM_USE_MPI=OFF"])


            if '~mkl' in spec:
                blas = self.spec['blas']
                lapack = self.spec['lapack']
                cmake_args.extend(['-DBLAS_DIR=%s' % blas.prefix])
                cmake_args.extend(['-DLAPACK_DIR=%s' % lapack.prefix])
                if "%gcc" in spec:
                    os.environ["LDFLAGS"] = "-lgfortran"

            cmake_args.extend(std_cmake_args)

            cmake(*cmake_args)
            make()
            make("install")
