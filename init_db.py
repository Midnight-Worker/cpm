from database import connect


def main():
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS packages (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                repo TEXT NOT NULL,
                asset_contains TEXT NOT NULL,

                include_source TEXT,
                lib_source TEXT,
                bin_source TEXT,

                include_target TEXT,
                lib_target TEXT,
                bin_target TEXT,

                cxxflags TEXT DEFAULT '',
                ldflags TEXT DEFAULT '',

                package_type TEXT DEFAULT 'generic'
            )
            """
        )

        conn.execute(
            """
            INSERT OR REPLACE INTO packages (
                name,
                repo,
                asset_contains,

                include_source,
                lib_source,
                bin_source,

                include_target,
                lib_target,
                bin_target,

                cxxflags,
                ldflags,

                package_type
            )
            VALUES (
                'slint',
                'slint-ui/slint',
                'cpp,linux,x86_64,.tar.gz',

                'include',
                'lib',
                'bin',

                'vendor/slint/include',
                'vendor/slint/lib',
                'vendor/slint/bin',

                '-Ivendor/slint/include/slint',
                '-Lvendor/slint/lib -Wl,-rpath,''$$ORIGIN/vendor/slint/lib'' -lslint_cpp',

                'slint'
            )
            """
        )

        conn.commit()

    print("cpm.db wurde angelegt.")


if __name__ == "__main__":
    main()
