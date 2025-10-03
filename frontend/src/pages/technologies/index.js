//import { Title, Container, Main } from '../../components'
//import styles from './styles.module.css'
//import MetaTags from 'react-meta-tags'
//
//const Technologies = () => {
//
//  return <Main>
//    <MetaTags>
//      <title>О проекте</title>
//      <meta name="description" content="Фудграм - Технологии" />
//      <meta property="og:title" content="О проекте" />
//    </MetaTags>
//
//    <Container>
//      <h1 className={styles.title}>Технологии</h1>
//      <div className={styles.content}>
//        <div>
//          <h2 className={styles.subtitle}>Технологии, которые применены в этом проекте:</h2>
//          <div className={styles.text}>
//            <ul className={styles.textItem}>
//              <li className={styles.textItem}>
//                Python
//              </li>
//              <li className={styles.textItem}>
//                Django
//              </li>
//              <li className={styles.textItem}>
//                Django REST Framework
//              </li>
//              <li className={styles.textItem}>
//                Djoser
//              </li>
//            </ul>
//          </div>
//        </div>
//      </div>
//
//    </Container>
//  </Main>
//}
//
//export default Technologies
//

import { Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const Technologies = () => {
  return (
    <Main>
      <MetaTags>
        <title>Технологии</title>
        <meta name="description" content="Фудграм — используемые технологии" />
        <meta property="og:title" content="Фудграм — Технологии" />
      </MetaTags>

      <Container>
        <h1 className={styles.title}>Технологии</h1>
        <div className={styles.content}>
          <section>
            <h2 className={styles.subtitle}>
              В проекте применены следующие технологии:
            </h2>

            <div className={styles.techGroups}>
              <div className={styles.group}>
                <h3 className={styles.groupTitle}>Бэкенд</h3>
                <ul className={styles.badges}>
                  <li className={styles.badge}>Python</li>
                  <li className={styles.badge}>Django</li>
                  <li className={styles.badge}>Django REST Framework</li>
                  <li className={styles.badge}>Djoser</li>
                </ul>
              </div>

              <div className={styles.group}>
                <h3 className={styles.groupTitle}>Фронтенд</h3>
                <ul className={styles.badges}>
                  <li className={styles.badge}>React</li>
                  <li className={styles.badge}>React Router</li>
                  <li className={styles.badge}>CSS-Modules</li>
                </ul>
              </div>

              <div className={styles.group}>
                <h3 className={styles.groupTitle}>Инфраструктура</h3>
                <ul className={styles.badges}>
                  <li className={styles.badge}>PostgreSQL</li>
                  <li className={styles.badge}>Docker / Docker Compose</li>
                  <li className={styles.badge}>Nginx + Gunicorn</li>
                </ul>
              </div>
            </div>
          </section>
        </div>
      </Container>
    </Main>
  )
}

export default Technologies
