
Scalar Spherical Harmonics
==========================

.. code:: python

    from pylayers.antprop.antenna import *
    from pylayers.antprop.antssh import *
    %matplotlib inline

.. parsed-literal::

    WARNING:traits.has_traits:DEPRECATED: traits.has_traits.wrapped_class, 'the 'implements' class advisor has been deprecated. Use the 'provides' class decorator.


.. code:: python

    A = Antenna('S1R1.mat',directory='ant/UWBAN/Matfile')
.. code:: python

    A



.. parsed-literal::

    FileName : S1R1.mat
    -----------------------
    fmin : 0.80GHz
    fmax : 5.95GHz
    step : 50.00MHz
    Nf : 104
    -----------------------
    Ntheta : 91
    Nphi : 180
    GmaxdB : 2.23 dB 
       f = 5.60 GHz 
       theta = 70.00 (degrees) 
       phi = 272.00  (degrees) 
    antenna name : Th1
    date : 04/12/12
    time : 15:55
    Notes : Mohamed at the log
    
    Serie : 1
    Run : 1
    Nb theta (lat) : 91
    Nb phi (lon) :180



To calculate scalar spherical harmonics use method ``ssh(A,L)``

.. code:: python

    L = 5
    A = ssh(A,L=5)
.. code:: python

    A



.. parsed-literal::

    FileName : S1R1.mat
    -----------------------
    fmin : 0.80GHz
    fmax : 5.95GHz
    step : 50.00MHz
    Nf : 104
    -----------------------
    Ntheta : 91
    Nphi : 180
    GmaxdB : 2.23 dB 
       f = 5.60 GHz 
       theta = 70.00 (degrees) 
       phi = 272.00  (degrees) 
    antenna name : Th1
    date : 04/12/12
    time : 15:55
    Notes : Mohamed at the log
    
    Serie : 1
    Run : 1
    Nb theta (lat) : 91
    Nb phi (lon) :180



.. code:: python

    plt.plot(abs(A.S.Cx.s2[0]))



.. parsed-literal::

    [<matplotlib.lines.Line2D at 0x2b81e3a10450>]




.. image:: AntennaSSH_files/AntennaSSH_7_1.png


.. code:: python

    A.savesh2()

.. parsed-literal::

    /home/uguen/Bureau/P1/ant/S1R1.sh2  already exist


.. code:: python

    A.loadsh2()
.. code:: python

    plt.plot(abs(A.S.Cx.s2[0]))



.. parsed-literal::

    [<matplotlib.lines.Line2D at 0x2b81e3b175d0>]




.. image:: AntennaSSH_files/AntennaSSH_10_1.png


.. code:: python

    A.S.s2tos3()
.. code:: python

    plt.plot(abs(A.S.Cx.s3[0]))



.. parsed-literal::

    [<matplotlib.lines.Line2D at 0x2b81e3be4550>]




.. image:: AntennaSSH_files/AntennaSSH_12_1.png


.. code:: python

    A.S.Cx.ind2.shape



.. parsed-literal::

    (36, 2)



.. code:: python

    A.savesh3()

.. parsed-literal::

    /home/uguen/Bureau/P1/ant/S1R1.sh3  already exist


.. code:: python

    plt.plot(abs(A.S.Cx.s2[0]))



.. parsed-literal::

    [<matplotlib.lines.Line2D at 0x2b81e3ca3b90>]




.. image:: AntennaSSH_files/AntennaSSH_15_1.png


.. code:: python

    A.loadsh3()
.. code:: python

    plt.plot(abs(A.S.Cx.s3[100]))



.. parsed-literal::

    [<matplotlib.lines.Line2D at 0x2b81e3d6e210>]




.. image:: AntennaSSH_files/AntennaSSH_17_1.png


.. code:: python

    plt.plot(abs(A.S.Cx.s2[100]))



.. parsed-literal::

    [<matplotlib.lines.Line2D at 0x2b81e3e3a050>]




.. image:: AntennaSSH_files/AntennaSSH_18_1.png


.. code:: python

    A.__dict__.keys()



.. parsed-literal::

    ['tau',
     'Nf',
     'PhotoFile',
     'Np',
     'Nt',
     'Run',
     'source',
     '_filename',
     'Serie',
     'Ftheta',
     'theta',
     'fromfile',
     'phi',
     'Fphi',
     'Notes',
     'fa',
     'S',
     'AntennaName',
     'typ',
     'DataFile',
     'evaluated',
     'Date',
     'ext',
     'StartTime',
     'SqG']



.. code:: python

    A.S.Cx.__dict__.keys()



.. parsed-literal::

    ['k2', 'ind3', 'ind2', 'fmax', 's2', 'Nf', 's3', 'lmax', 'fmin']



.. code:: python

    A.S.Cx



.. parsed-literal::

    Nf   : 104
    fmin (GHz) : 0.8
    fmax (GHz) : 5.95
    NCoeff s2  : 36
    Ncoeff s3 : 143


