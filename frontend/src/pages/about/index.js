import { Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const About = ({
  githubUrl = 'https://github.com/Marakes/foodgram',
  authorName = 'Marakes',
  authorUrl = 'https://github.com/Marakes',
}) => {
  return (
    <Main>
      <MetaTags>
        <title>О проекте</title>
        <meta name="description" content="Фудграм — платформа для хранения и обмена рецептами" />
        <meta property="og:title" content="О проекте — Фудграм" />
      </MetaTags>

      <Container>
        <header className={styles.header}>
          <h1 className={styles.title}>Привет! 👋</h1>
          <p className={styles.leadCentered}>
            Foodgram — мой пет-проект из Practicum: от бэкенда до чутки интерфейса.
            Здесь удобно публиковать рецепты, подписываться на авторов
            и выгружать список покупок.
          </p>
        </header>

        <div className={styles.content}>
          <section className={styles.section}>
            <h2 className={styles.subtitle}>Как это работает</h2>

            <ol className={styles.steps}>
              <li className={styles.step}>
                <span className={styles.stepNum} aria-hidden>1</span>
                Зарегистрируйтесь и заполните профиль (e-mail-подтверждение не требуется).
              </li>
              <li className={styles.step}>
                <span className={styles.stepNum} aria-hidden>2</span>
                Создайте рецепт: добавьте фото, ингредиенты и шаги приготовления.
              </li>
              <li className={styles.step}>
                <span className={styles.stepNum} aria-hidden>3</span>
                Сохраняйте в избранное, подписывайтесь на авторов и скачивайте список покупок.
              </li>
            </ol>

            <div className={`${styles.ctaRow} ${styles.ctaRowSplit}`}>
              <div className={styles.ctaTop}>
                <a className={styles.buttonPrimary} href="/recipes">Посмотреть рецепты</a>
                <a className={styles.buttonGhost} href="/recipes/create">Добавить рецепт</a>
              </div>
              <div className={styles.ctaBottom}>
                <a className={styles.buttonGhost} href="/technologies">Технологии проекта</a>
              </div>
            </div>

            <div className={styles.note}>
              Поддерживается поиск по ингредиентам и автоформирование списка покупок — попробуйте на своей кухне 🙂
            </div>
          </section>

          <aside className={styles.aside}>
            <h2 className={styles.additionalTitle}>Ссылки</h2>
            <div className={styles.card}>
              <div className={styles.linksRow}>
                <span className={styles.muted}>Репозиторий:</span>
                <a href={githubUrl} className={styles.textLink}> GitHub проекта</a>
              </div>
              <div className={styles.linksRow}>
                <span className={styles.muted}>Автор:</span>
                <a href={authorUrl} className={styles.textLink}> {authorName}</a>
              </div>
            </div>

            <h3 className={styles.additionalTitleSmall}>FAQ</h3>
            <div className={styles.card}>
              <div className={styles.faqItem}>
                <div className={styles.faqQ}>Нужно ли подтверждать e-mail?</div>
                <div className={styles.faqA}>Нет, можно указать любой адрес.</div>
              </div>
              <div className={styles.faqItem}>
                <div className={styles.faqQ}>Можно ли смотреть без регистрации?</div>
                <div className={styles.faqA}>Да, но без публикации, избранного и подписок.</div>
              </div>
              <div className={styles.faqItem}>
                <div className={styles.faqQ}>Где посмотреть стек?</div>
                <div className={styles.faqA}>На странице «Технологии».</div>
              </div>
            </div>
          </aside>
        </div>
      </Container>
    </Main>
  )
}

export default About
