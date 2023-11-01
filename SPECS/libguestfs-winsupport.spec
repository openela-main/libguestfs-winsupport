%global         ntfs_version 2022.10.3
%global         compression_version 1.0

# debuginfo makes no sense for this package, so disable it
%global         debug_package %{nil}

Name:           libguestfs-winsupport
Version:        8.8
Release:        2%{?dist}
Summary:        Add support for Windows guests to virt-v2v and virt-p2v

URL:            https://www.tuxera.com/company/open-source/
# and URL:      https://github.com/ebiggers/ntfs-3g-system-compression
License:        GPLv2+

# This package shouldn't be installed without installing the base
# libguestfs package.
Requires:       libguestfs >= 1:1.38.2

# Source and patches for ntfs-3g and ntfs-3g-system-compression.
Source0:        http://tuxera.com/opensource/ntfs-3g_ntfsprogs-%{ntfs_version}.tgz
Source1:        https://github.com/ebiggers/ntfs-3g-system-compression/archive/v%{version}/ntfs-3g-system-compression-%{compression_version}.tar.gz

Patch0:         ntfs-3g_ntfsprogs-2011.10.9-RC-ntfsck-unsupported-return-0.patch

BuildRequires:  make
BuildRequires:  gcc
BuildRequires:  libtool, libattr-devel
BuildRequires:  libconfig-devel, libgcrypt-devel, gnutls-devel, libuuid-devel
BuildRequires:  autoconf, automake, libtool, fuse-devel


%description
This optional package adds support for Windows guests (NTFS) to the
virt-v2v and virt-p2v programs.

This package also supports system compression ("Compact OS") using the
plugin from https://github.com/ebiggers/ntfs-3g-system-compression


%prep
%setup -q -n ntfs-3g_ntfsprogs-%{ntfs_version}
%setup -n ntfs-3g_ntfsprogs-%{ntfs_version} -T -D -a 1
%patch0 -p1 -b .unsupported


%build
CFLAGS="$RPM_OPT_FLAGS -D_FILE_OFFSET_BITS=64"
%configure \
        --disable-static \
        --disable-ldconfig \
        --with-fuse=external \
        --exec-prefix=/ \
        --enable-posix-acls \
        --enable-xattr-mappings \
        --enable-crypto \
        --enable-extras \
        --enable-quarantined
%make_build LIBTOOL=%{_bindir}/libtool

# Build ntfs-3g-system-compression plugin.
pushd ntfs-3g-system-compression-%{compression_version}
autoreconf -i
# Trick the plugin into using the just-compiled ntfs-3g.
cp ../libntfs-3g/libntfs-3g.pc .
sed -i \
    -e 's,^libdir=.*,libdir=../libntfs-3g,' \
    -e 's,^includedir=.*,includedir=../include,' \
    libntfs-3g.pc
export PKG_CONFIG_PATH=.
%configure
%make_build
popd


%install
# Build it into a destdir which is not the final buildroot.
mkdir destdir
make LIBTOOL=%{_bindir}/libtool DESTDIR=$(pwd)/destdir install
rm -rf destdir/%{_libdir}/*.la
rm -rf destdir/%{_libdir}/*.a

rm -rf destdir/%{_sbindir}/mount.ntfs-3g
cp -a destdir/%{_bindir}/ntfs-3g destdir/%{_sbindir}/mount.ntfs-3g

# Actually make some symlinks for simplicity...
# ... since we're obsoleting ntfsprogs-fuse
pushd destdir/%{_bindir}
ln -s ntfs-3g ntfsmount
popd
pushd destdir/%{_sbindir}
ln -s mount.ntfs-3g mount.ntfs-fuse
# And since there is no other package in Fedora that provides an ntfs 
# mount...
ln -s mount.ntfs-3g mount.ntfs
# Need this for fsck to find it
ln -s ../bin/ntfsck fsck.ntfs
popd
mv destdir/sbin/* destdir/%{_sbindir}
rmdir destdir/sbin

# We get this on our own, thanks.
rm -r destdir/%{_defaultdocdir}

# Remove development files.
rm -r destdir/%{_includedir}
rm -r destdir/%{_libdir}/pkgconfig

# Install ntfs-3g-system-compression plugin in the same place.
pushd ntfs-3g-system-compression-%{compression_version}
%make_install DESTDIR=$(pwd)/../destdir
popd
rm -rf destdir/%{_libdir}/ntfs-3g/*.la

# Take the destdir and put it into a tarball for the libguestfs appliance.
mkdir -p %{buildroot}%{_libdir}/guestfs/supermin.d
pushd destdir
tar zvcf %{buildroot}%{_libdir}/guestfs/supermin.d/zz-winsupport.tar.gz .
popd


%files
%doc AUTHORS ChangeLog COPYING CREDITS NEWS README
%{_libdir}/guestfs/supermin.d/zz-winsupport.tar.gz


%changelog
* Thu Aug 31 2023 Richard W.M. Jones <rjones@redhat.com> - 8.8-2
- Rebase to ntfs-3g 2022.10.3
- Fixes: CVE-2022-40284
- resolves: rhbz#2236371

* Mon Sep 26 2022 Richard W.M. Jones <rjones@redhat.com> - 8.8-1
- Rebase to ntfs-3g 2022.5.17
- Fixes: CVE-2021-46790, CVE-2022-30783, CVE-2022-30784, CVE-2022-30785,
  CVE-2022-30786, CVE-2022-30787, CVE-2022-30788, CVE-2022-30789
  resolves: rhbz#2127240 rhbz#2127248
  (also: 2127233 2127234 2127241 2127249 2127255 2127256 2127262 2127263)

* Fri Sep 17 2021 Richard W.M. Jones <rjones@redhat.com> - 8.6-1
- Rebase to ntfs-3g 2021.8.22
- Fixes: CVE-2021-33285, CVE-2021-33286, CVE-2021-33287, CVE-2021-33289,
  CVE-2021-35266, CVE-2021-35267, CVE-2021-35268, CVE-2021-35269,
  CVE-2021-39251, CVE-2021-39252, CVE-2021-39253, CVE-2021-39254
  resolves: rhbz#2004490

* Thu Sep 2 2021 Danilo C. L. de Paula <ddepaula@redhat.com> - 8.2-1.el8
- Resolves: bz#2000225
  (Rebase virt:rhel module:stream based on AV-8.6)

* Mon Apr 27 2020 Danilo C. L. de Paula <ddepaula@redhat.com> - 8.2
- Resolves: bz#1810193
  (Upgrade components in virt:rhel module:stream for RHEL-8.3 release)

* Fri Jun 28 2019 Danilo de Paula <ddepaula@redhat.com> - 8.0-4
- Rebuild all virt packages to fix RHEL's upgrade path
- Resolves: rhbz#1695587
  (Ensure modular RPM upgrade path)

* Wed Apr 10 2019 Richard W.M. Jones <rjones@redhat.com> - 8.0-3
- Fix for CVE-2019-9755
  (heap-based buffer overflow leads to local root privilege escalation)
  resolves: rhbz#1698503

* Mon Jul 16 2018 Richard W.M. Jones <rjones@redhat.com> - 8.0-2
- Fix for ntfsclone crash (RHBZ#1601146).

* Wed Jul 11 2018 Richard W.M. Jones <rjones@redhat.com> - 8.0-1
- Rebase to 2017.3.23.
- Remove patches which are now upstream.
- Resynch with Fedora package.
- Enable all architectures for RHEL 8.

* Wed Feb 22 2017 Richard W.M. Jones <rjones@redhat.com> - 7.2-2
- Fix for handling guest filenames with invalid or incomplete
  multibyte or wide characters
  resolves: rhbz#1301593

* Tue Jul 07 2015 Richard W.M. Jones <rjones@redhat.com> - 7.2-1
- Rebase and rebuild for RHEL 7.2
  resolves: rhbz#1240278

* Tue Jun 30 2015 Richard W.M. Jones <rjones@redhat.com> - 7.1-6
- Bump version and rebuild.
  related: rhbz#1221583

* Fri May 15 2015 Richard W.M. Jones <rjones@redhat.com> - 7.1-5
- Enable aarch64 architecture.
  resolves: rhbz#1221583

* Thu Aug 28 2014 Richard W.M. Jones <rjones@redhat.com> - 7.1-4
- Enable debuginfo support and stripping.
  resolves: rhbz#1100319

* Thu Aug 28 2014 Richard W.M. Jones <rjones@redhat.com> - 7.1-3
- Add patches from Fedora package which add fstrim support.
  resolves: rhbz#1100319

* Mon Jul 21 2014 Richard W.M. Jones <rjones@redhat.com> - 7.1-2
- New package for RHEL 7.1
- Rebase to ntfs-3g 2014.2.15
  resolves: rhbz#1100319
- Change the package so it works with supermin5.
- Remove dependency on external FUSE.

* Wed Apr  3 2013 Richard W.M. Jones <rjones@redhat.com> - 7.0-2
- Resync against Rawhide package (ntfs-3g 2013.1.13).
- Drop HAL file since HAL is dead.
  resolves: rhbz#819939

* Thu Dec 20 2012 Richard W.M. Jones <rjones@redhat.com> - 7.0-1
- New package for RHEL 7
  resolves: rhbz#819939
- Resync against Rawhide package.

* Mon Mar 28 2011 Richard W.M. Jones <rjones@redhat.com> - 1.0-7
- Disable debuginfo package.
  resolves: RHBZ#691555.

* Tue Mar  8 2011 Richard W.M. Jones <rjones@redhat.com> - 1.0-6
- Require libguestfs 1.7.17 (newer version in RHEL 6.1).
- Require febootstrap-supermin-helper instead of febootstrap
  resolves: RHBZ#670299.

* Thu Jul  1 2010 Richard W.M. Jones <rjones@redhat.com> - 1.0-5
- Make sure intermediate lib* directories are created in hostfiles (RHBZ#603429)

* Thu Jun  3 2010 Richard W.M. Jones <rjones@redhat.com> - 1.0-4
- Requires fuse-libs (RHBZ#599300).

* Fri May 21 2010 Richard W.M. Jones <rjones@redhat.com> - 1.0-3
- ExclusiveArch x86_64.

* Tue May 18 2010 Richard W.M. Jones <rjones@redhat.com> - 1.0-2
- Package Windows support for libguestfs.
