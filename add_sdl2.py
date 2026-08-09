from database import connect

with connect() as conn:
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
            'sdl2',
            'libsdl-org/SDL',
            'linux,x86_64,.tar.gz',

            'include',
            'lib',
            NULL,

            'vendor/sdl2/include',
            'vendor/sdl2/lib',
            NULL,

            '-Ivendor/sdl2/include',
            '-Lvendor/sdl2/lib -lSDL2',

            'generic'
        )
        """
    )

    conn.commit()

print("SDL2 wurde eingetragen.")
