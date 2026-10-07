// Campus photography used in the editorial sections (Problem 10). All from Wikimedia Commons under free
// licenses; credited in the photo corners and in the site footer, as the licenses require.

export interface Photo {
  src: string
  alt: string
  author: string
  license: string
  licenseUrl: string
  source: string
}

export const PHOTOS = {
  hero: {
    src: '/images/hero-harkness-blue-sky.jpg',
    alt: 'Harkness Tower rising into a clear blue autumn sky above Yale',
    author: 'Hrichardson (WMF)',
    license: 'CC BY-SA 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0/',
    source: 'https://commons.wikimedia.org/wiki/File:Harkness_Tower_Yale_Fall_2014.jpg',
  },
  oldCampus: {
    src: '/images/old-campus-students.jpg',
    alt: 'Students walking across the Old Campus courtyard by Durfee Hall',
    author: 'DimiTalen',
    license: 'CC0',
    licenseUrl: 'https://creativecommons.org/publicdomain/zero/1.0/',
    source:
      'https://commons.wikimedia.org/wiki/File:Old_Campus_Courtyard_and_Durfee_Hall,_Yale_University,_New_Haven,_2007.jpg',
  },
  gate: {
    src: '/images/memorial-quad-gate.jpg',
    alt: 'Wrought-iron Memorial Quadrangle gate with "Lux et Veritas" worked into the ironwork',
    author: 'Steven J. Baskauf',
    license: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
    source: 'https://commons.wikimedia.org/wiki/File:Memorial_Quad_gate_Yale.jpg',
  },
  street: {
    src: '/images/harkness-autumn-street.jpg',
    alt: 'Autumn trees on a New Haven street with Harkness Tower in the distance',
    author: 'ajay_suresh',
    license: 'CC BY 2.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/2.0/',
    source: 'https://commons.wikimedia.org/wiki/File:Harkness_Tower_-_Yale_University_(54106458290).jpg',
  },
} satisfies Record<string, Photo>

export function PhotoCredit({ photo }: { photo: Photo }) {
  return (
    <a className="photo-credit" href={photo.source} target="_blank" rel="noreferrer">
      Photo: {photo.author} · {photo.license}
    </a>
  )
}
